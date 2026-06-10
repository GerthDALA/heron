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
