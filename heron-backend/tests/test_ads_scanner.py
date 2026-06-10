"""Ads copy scan pipeline tests — engine unit tests + API route tests."""

import time

import pytest

from app.engine.ads_scanner import AdsScanner, normalise_input_text
from app.engine.risk_calculator import RiskCalculator


@pytest.fixture
def ads_scanner(regex_engine):
    return AdsScanner(regex_engine, RiskCalculator())


def test_eco_responsable_in_ad_copy(ads_scanner):
    claims = ads_scanner.scan_text(
        "Découvrez notre formule éco-responsable, idéale pour votre routine.",
        "ad_copy", 1_000_000,
    )
    assert any(c["risk_level"] == "high" and c["empco_article"] == "Annexe I, Point 4a"
               for c in claims)


def test_carbon_neutral_in_email(ads_scanner):
    claims = ads_scanner.scan_text(
        "Our brand will be carbon neutral by 2030 — join the movement!",
        "email", 1_000_000,
    )
    assert any(c["risk_level"] == "high" and c["empco_article"] == "Annexe I, Point 4c"
               for c in claims)


def test_fabrique_de_maniere_responsable(ads_scanner):
    claims = ads_scanner.scan_text(
        "Fabriqué de manière responsable dans nos ateliers.",
        "social_post", 1_000_000,
    )
    assert any(c["risk_level"] == "high" and c["empco_article"] == "Annexe I, Point 4a"
               for c in claims)


def test_certified_cosmos_no_match(ads_scanner):
    claims = ads_scanner.scan_text(
        "Certifié COSMOS Organic par Ecocert.", "ad_copy", 1_000_000,
    )
    assert claims == []


def test_html_is_stripped_before_scanning(ads_scanner):
    claims = ads_scanner.scan_text(
        "<div class='eco'><b>formule</b> <i>eco-responsable</i></div>",
        "ad_copy", 1_000_000,
    )
    assert any("eco-responsable" in c["matched_text"].lower() for c in claims)
    # The HTML attribute value 'eco' must not appear in any matched text
    assert all("<" not in c["matched_text"] for c in claims)


def test_normalise_collapses_whitespace():
    assert normalise_input_text("a   b\n\n\nc\t d") == "a b c d"


def test_transcript_plain_text_scanned(ads_scanner):
    claims = ads_scanner.scan_text(
        "et donc notre nouvelle gamme est totalement naturelle et respectueuse",
        "transcript", 1_000_000,
    )
    assert any(c["risk_level"] == "high" for c in claims)


def test_exposure_priced_per_claim(ads_scanner):
    claims = ads_scanner.scan_text(
        "Formule eco-responsable.", "ad_copy", 2_000_000,
    )
    assert claims[0]["exposure_eur"] == 200_000.0  # 2M × 10% × 1.0


def test_scan_is_fast(ads_scanner):
    text = ("Notre marque propose des produits de qualité. " * 100)[:5000]
    start = time.monotonic()
    ads_scanner.scan_text(text, "ad_copy", 1_000_000)
    assert time.monotonic() - start < 2.0


# --- API route tests ---

def _register(client, email="ads@test.fr"):
    r = client.post("/api/v1/auth/register", json={"email": email, "password": "motdepasse123"})
    return r.json()["access_token"]


def test_ads_scan_freemium_redacts(client):
    response = client.post("/api/v1/ads/scan", json={
        "input_type": "ad_copy",
        "input_title": "Meta Ad — Sérum Vitamine C",
        "input_text": "Sérum eco-responsable, naturel et carbon neutral. Achetez maintenant!",
        "annual_revenue_eur": 1_000_000,
        "email": "prospect@test.fr",
    })
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["status"] == "complete"
    assert body["is_freemium"] is True
    assert body["total_claims"] >= 3
    assert len(body["visible_claims"]) == 1
    assert body["redacted_count"] == body["total_claims"] - 1
    for claim in body["visible_claims"]:
        assert claim["replacement_text"] is None  # paywall


def test_ads_scan_freemium_requires_email(client):
    response = client.post("/api/v1/ads/scan", json={
        "input_type": "ad_copy",
        "input_text": "Formule eco-responsable pour tous.",
        "annual_revenue_eur": 1_000_000,
    })
    assert response.status_code == 422


def test_ads_scan_too_short_rejected(client):
    response = client.post("/api/v1/ads/scan", json={
        "input_type": "ad_copy",
        "input_text": "court",
        "annual_revenue_eur": 1_000_000,
        "email": "a@b.fr",
    })
    assert response.status_code == 422


def test_ads_scan_too_long_rejected(client):
    response = client.post("/api/v1/ads/scan", json={
        "input_type": "ad_copy",
        "input_text": "x" * 50_001,
        "annual_revenue_eur": 1_000_000,
        "email": "a@b.fr",
    })
    assert response.status_code == 422


def test_ads_scan_invalid_input_type(client):
    response = client.post("/api/v1/ads/scan", json={
        "input_type": "video",
        "input_text": "Formule eco-responsable pour tous.",
        "annual_revenue_eur": 1_000_000,
        "email": "a@b.fr",
    })
    assert response.status_code == 422


def test_ads_scan_authenticated_shows_all(client):
    token = _register(client)
    response = client.post(
        "/api/v1/ads/scan",
        json={
            "input_type": "email",
            "input_title": "Newsletter juin",
            "input_text": "Notre gamme naturelle et eco-responsable arrive. Carbon neutral by 2030.",
            "annual_revenue_eur": 1_000_000,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["is_freemium"] is False
    assert body["redacted_count"] == 0
    assert len(body["visible_claims"]) == body["total_claims"] >= 3


def test_ads_scan_pdf_uses_input_title(client):
    token = _register(client, "adspdf@test.fr")
    scan = client.post(
        "/api/v1/ads/scan",
        json={
            "input_type": "ad_copy",
            "input_title": "Campagne Printemps",
            "input_text": "Une formule eco-responsable signée Maison Test.",
            "annual_revenue_eur": 1_000_000,
        },
        headers={"Authorization": f"Bearer {token}"},
    ).json()
    response = client.get(
        f"/api/v1/ads/scan/{scan['scan_id']}/pdf",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.content[:5] == b"%PDF-"


def test_ads_scan_get_requires_ownership_or_email(client):
    freemium = client.post("/api/v1/ads/scan", json={
        "input_type": "social_post",
        "input_text": "Notre collection la plus durable à ce jour!",
        "annual_revenue_eur": 1_000_000,
        "email": "owner@freemium.fr",
    }).json()
    scan_id = freemium["scan_id"]

    assert client.get(f"/api/v1/ads/scan/{scan_id}").status_code == 403
    ok = client.get(f"/api/v1/ads/scan/{scan_id}", params={"email": "owner@freemium.fr"})
    assert ok.status_code == 200
    assert ok.json()["scan"]["input_type"] == "social_post"
