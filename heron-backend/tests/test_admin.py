"""Admin surface tests: gating, evidence review, scan browsing, corpus reload."""

import pytest


@pytest.fixture
def admin_client(client, monkeypatch):
    """Client with admin@test.fr granted admin rights."""
    monkeypatch.setenv("ADMIN_EMAILS", '["admin@test.fr"]')
    from app.config import get_settings
    get_settings.cache_clear()
    yield client
    get_settings.cache_clear()


def _register(client, email):
    r = client.post("/api/v1/auth/register", json={"email": email, "password": "motdepasse123"})
    assert r.status_code == 201
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def test_admin_routes_require_admin_email(admin_client):
    headers = _register(admin_client, "regular@test.fr")
    assert admin_client.get("/api/v1/admin/stats", headers=headers).status_code == 403
    assert admin_client.get("/api/v1/admin/stats").status_code == 401


def test_admin_stats(admin_client):
    headers = _register(admin_client, "admin@test.fr")
    response = admin_client.get("/api/v1/admin/stats", headers=headers)
    assert response.status_code == 200
    stats = response.json()
    assert stats["corpora"] == 3
    assert stats["legal_articles"] == 11
    # Every corpus article is now verified against its official source
    assert stats["articles_pending_source"] == 0
    assert "scans_by_status" in stats


def test_admin_evidence_review_flow(admin_client):
    admin_headers = _register(admin_client, "admin@test.fr")
    user_headers = _register(admin_client, "brand@test.fr")

    upload = admin_client.post(
        "/api/v1/evidence",
        data={
            "cert_type_id": "GOTS", "cert_number": "G-77",
            "cert_holder": "Textile Co", "issuer_name": "Global Standard",
            "issue_date": "2026-02-01", "scope": "coton biologique",
        },
        headers=user_headers,
    )
    evidence_id = upload.json()["evidence_id"]

    queue = admin_client.get("/api/v1/admin/evidence", params={"verified": 0},
                             headers=admin_headers).json()
    assert any(e["id"] == evidence_id for e in queue["evidence"])
    entry = next(e for e in queue["evidence"] if e["id"] == evidence_id)
    assert entry["user_email"] == "brand@test.fr"
    assert entry["verified_label"] == "unverified"

    verify = admin_client.post(
        f"/api/v1/admin/evidence/{evidence_id}/verify",
        json={"verified": 2},
        headers=admin_headers,
    )
    assert verify.status_code == 200
    assert verify.json()["verified_label"] == "admin-verified"

    # The owner sees the new status
    listing = admin_client.get("/api/v1/evidence", headers=user_headers).json()
    assert listing["evidence"][0]["verified"] == 2

    # Regular users cannot verify
    assert admin_client.post(
        f"/api/v1/admin/evidence/{evidence_id}/verify",
        json={"verified": 0}, headers=user_headers,
    ).status_code == 403


def test_admin_browse_scans(admin_client, fake_homepage):
    admin_headers = _register(admin_client, "admin@test.fr")
    admin_client.post("/api/v1/freemium/scan", json={
        "domain": "marque.fr", "annual_revenue_eur": 1000000, "email": "p@test.fr",
    })
    response = admin_client.get("/api/v1/admin/scans", headers=admin_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["total"] >= 1
    assert body["scans"][0]["domain"] == "marque.fr"

    ads = admin_client.get("/api/v1/admin/scans", params={"scan_type": "ads"},
                           headers=admin_headers).json()
    assert ads["scan_type"] == "ads"


def test_admin_corpus_reload(admin_client):
    headers = _register(admin_client, "admin@test.fr")
    response = admin_client.post("/api/v1/admin/corpus/reload", headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert body["corpora_loaded"] == 3
    assert body["articles_loaded"] == 11


def test_admin_expiry_check_trigger(admin_client):
    headers = _register(admin_client, "admin@test.fr")
    response = admin_client.post("/api/v1/admin/evidence/expiry-check", headers=headers)
    assert response.status_code == 200
    assert "notices_sent" in response.json()
