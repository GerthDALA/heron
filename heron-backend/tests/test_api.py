"""API route tests via the FastAPI test client (httpx transport)."""

import pytest


@pytest.fixture
def fake_homepage(monkeypatch):
    async def fake_crawl_homepage(domain):
        return {
            "url": "https://marque.fr",
            "title": "Marque",
            "body_text": "Formule eco-responsable et naturelle. Carbon neutral by 2030.",
        }

    from app.engine import crawler
    monkeypatch.setattr(crawler, "crawl_homepage", fake_crawl_homepage)


def register(client, email="user@test.fr", password="motdepasse123"):
    response = client.post("/api/v1/auth/register", json={"email": email, "password": password})
    assert response.status_code == 201, response.text
    return response.json()["access_token"]


def auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


def test_health(client):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_register_and_login(client):
    register(client, "alice@test.fr")
    response = client.post("/api/v1/auth/login",
                           json={"email": "alice@test.fr", "password": "motdepasse123"})
    assert response.status_code == 200
    assert response.json()["access_token"]


def test_register_duplicate_email_rejected(client):
    register(client, "bob@test.fr")
    response = client.post("/api/v1/auth/register",
                           json={"email": "bob@test.fr", "password": "motdepasse123"})
    assert response.status_code == 409


def test_login_wrong_password(client):
    register(client, "carol@test.fr")
    response = client.post("/api/v1/auth/login",
                           json={"email": "carol@test.fr", "password": "wrong-password"})
    assert response.status_code == 401


def test_scan_requires_auth(client):
    response = client.post("/api/v1/scan",
                           json={"domain": "marque.fr", "annual_revenue_eur": 1000000})
    assert response.status_code == 401


def test_scan_rejected_on_free_plan(client):
    token = register(client, "dave@test.fr")
    response = client.post(
        "/api/v1/scan",
        json={"domain": "marque.fr", "annual_revenue_eur": 1000000, "plan_tier": "starter"},
        headers=auth_headers(token),
    )
    assert response.status_code == 403


def test_freemium_scan_no_auth(client, fake_homepage):
    response = client.post("/api/v1/freemium/scan", json={
        "domain": "marque.fr",
        "annual_revenue_eur": 1000000,
        "email": "prospect@test.fr",
    })
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["scan_id"]
    assert body["domain"] == "marque.fr"
    assert len(body["visible_claims"]) == 1
    assert body["redacted_count"] >= 1
    assert body["total_exposure_eur"] > 0
    assert "checkout" in body["cta_url"]
    # Constraint 4: freemium never returns replacement text
    for claim in body["visible_claims"]:
        assert claim["replacement_text"] is None


def test_scan_ownership_enforced(client, fake_homepage):
    token_a = register(client, "owner@test.fr")
    token_b = register(client, "intruder@test.fr")

    # create a scan row directly through the freemium path, then re-own it
    freemium = client.post("/api/v1/freemium/scan", json={
        "domain": "marque.fr", "annual_revenue_eur": 1000000, "email": "owner@test.fr",
    }).json()
    scan_id = freemium["scan_id"]

    # neither user owns a freemium (user_id NULL) scan
    response = client.get(f"/api/v1/scan/{scan_id}", headers=auth_headers(token_a))
    assert response.status_code == 403
    response = client.get(f"/api/v1/scan/{scan_id}", headers=auth_headers(token_b))
    assert response.status_code == 403


def test_get_scan_not_found(client):
    token = register(client, "erin@test.fr")
    response = client.get("/api/v1/scan/does-not-exist", headers=auth_headers(token))
    assert response.status_code == 404


def test_report_requires_auth(client):
    response = client.get("/api/v1/report/whatever")
    assert response.status_code == 401


def test_billing_checkout_requires_auth(client):
    response = client.post("/api/v1/billing/checkout", json={"plan": "starter"})
    assert response.status_code == 401


def test_billing_webhook_always_200(client):
    # Invalid signature: Stripe still requires a 200 response
    response = client.post("/api/v1/billing/webhook", content=b"{}",
                           headers={"Stripe-Signature": "bogus"})
    assert response.status_code == 200


def test_checkout_completed_claims_freemium_scan(client, fake_homepage):
    """After paying, the user must own the freemium scan they upgraded from."""
    import asyncio

    token = _freemium_owner_token = register(client, "buyer@test.fr")
    freemium = client.post("/api/v1/freemium/scan", json={
        "domain": "marque.fr", "annual_revenue_eur": 1000000, "email": "buyer@test.fr",
    }).json()
    scan_id = freemium["scan_id"]

    # Before checkout: scan is unowned, access denied
    assert client.get(f"/api/v1/scan/{scan_id}", headers=auth_headers(token)).status_code == 403

    # Simulate the Stripe checkout.session.completed webhook handling
    me = client.post("/api/v1/auth/login",
                     json={"email": "buyer@test.fr", "password": "motdepasse123"})
    from app.database import _connect
    from app.services.billing_service import handle_checkout_completed
    from app.services.auth_service import decode_token

    user_id = decode_token(token)["sub"]
    event = {"data": {"object": {
        "customer": "cus_test123",
        "metadata": {"user_id": user_id, "plan": "starter", "scan_id": scan_id},
    }}}

    async def run():
        db = await _connect()
        try:
            return await handle_checkout_completed(db, event)
        finally:
            await db.close()

    returned_scan_id = asyncio.run(run())
    assert returned_scan_id == scan_id

    # After checkout: scan is owned and accessible
    response = client.get(f"/api/v1/scan/{scan_id}", headers=auth_headers(token))
    assert response.status_code == 200


def test_freemium_scan_refuses_private_host(client):
    """SSRF guard: unauthenticated scans must not reach internal addresses."""
    response = client.post("/api/v1/freemium/scan", json={
        "domain": "127.0.0.1:8080",
        "annual_revenue_eur": 1000000,
        "email": "attacker@test.fr",
    })
    assert response.status_code == 422
    assert "private" in response.json()["detail"].lower()


def test_evidence_upload_list_download_roundtrip(client):
    token = register(client, "certowner@test.fr")
    pdf_bytes = b"%PDF-1.4 fake cosmos certificate"
    upload = client.post(
        "/api/v1/evidence",
        data={
            "cert_type_id": "COSMOS", "cert_number": "C-42",
            "cert_holder": "Maison Test", "issuer_name": "Ecocert",
            "issue_date": "2026-01-01", "valid_until": "2028-01-01",
            "scope": "gamme soins",
        },
        files={"file": ("cert.pdf", pdf_bytes, "application/pdf")},
        headers=auth_headers(token),
    )
    assert upload.status_code == 201, upload.text
    evidence_id = upload.json()["evidence_id"]

    listing = client.get("/api/v1/evidence", headers=auth_headers(token)).json()
    assert listing["evidence"][0]["file_url"] == f"/api/v1/evidence/{evidence_id}/file"

    download = client.get(f"/api/v1/evidence/{evidence_id}/file", headers=auth_headers(token))
    assert download.status_code == 200
    assert download.content == pdf_bytes

    summary = client.get("/api/v1/evidence/summary", headers=auth_headers(token)).json()
    assert summary["active_certs"] == 1
    assert "EMPCO_2024_825_ANNEX_4A" in summary["covered_articles"]

    # Another user cannot download it
    other = register(client, "other@test.fr")
    assert client.get(f"/api/v1/evidence/{evidence_id}/file",
                      headers=auth_headers(other)).status_code == 404
