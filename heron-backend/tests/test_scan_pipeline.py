"""End-to-end scan pipeline test with the crawler mocked out."""

import asyncio
import uuid
from datetime import datetime, timezone

import pytest

FAKE_PAGES = [
    {
        "url": "https://marque.fr/produit/serum",
        "title": "Sérum",
        "body_text": "Notre formule eco-responsable aux ingredients naturels. "
                     "Nous serons carbon neutral en 2030.",
    },
    {
        "url": "https://marque.fr/collection/soins",
        "title": "Soins",
        "body_text": "Notre collection la plus durable à ce jour. Fabriqué en France.",
    },
]


@pytest.fixture
def fake_crawler(monkeypatch):
    async def fake_crawl_domain(domain, max_pages):
        return FAKE_PAGES

    async def fake_crawl_homepage(domain):
        return FAKE_PAGES[0]

    from app.engine import crawler
    monkeypatch.setattr(crawler, "crawl_domain", fake_crawl_domain)
    monkeypatch.setattr(crawler, "crawl_homepage", fake_crawl_homepage)


async def _create_user_and_scan(db_path: str) -> str:
    from app.database import _connect
    db = await _connect(db_path)
    try:
        user_id = str(uuid.uuid4())
        scan_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        await db.execute(
            "INSERT INTO users (id, email, password_hash, plan, created_at) "
            "VALUES (?, 'test@heron.app', 'x', 'starter', ?)",
            (user_id, now),
        )
        await db.execute(
            "INSERT INTO scans (id, user_id, domain, annual_revenue_eur, status, is_freemium, created_at) "
            "VALUES (?, ?, 'marque.fr', 2000000, 'pending', 0, ?)",
            (scan_id, user_id, now),
        )
        await db.commit()
        return scan_id
    finally:
        await db.close()


def test_full_scan_pipeline(initialized_db, fake_crawler):
    from app.database import _connect
    from app.services.scan_service import run_full_scan

    async def run():
        scan_id = await _create_user_and_scan(initialized_db)
        await run_full_scan(scan_id)

        db = await _connect(initialized_db)
        try:
            cursor = await db.execute("SELECT * FROM scans WHERE id = ?", (scan_id,))
            scan = dict(await cursor.fetchone())
            cursor = await db.execute(
                "SELECT * FROM claims WHERE scan_id = ? ORDER BY exposure_eur DESC", (scan_id,)
            )
            claims = [dict(r) for r in await cursor.fetchall()]
            cursor = await db.execute("SELECT * FROM reports WHERE scan_id = ?", (scan_id,))
            report = await cursor.fetchone()
        finally:
            await db.close()
        return scan, claims, report

    scan, claims, report = asyncio.run(run())

    assert scan["status"] == "complete"
    assert scan["pages_scanned"] == 2
    assert scan["total_claims"] == len(claims) > 0
    assert scan["total_exposure_eur"] == round(sum(c["exposure_eur"] for c in claims), 2)

    articles = {c["empco_article"] for c in claims}
    assert "Annexe I, Point 4a" in articles
    assert "Annexe I, Point 4c" in articles  # offset-based carbon claims
    assert "Annexe I, Point 4b" in articles  # single-aspect superlatives

    # high 4a claim on 2M revenue = 200,000 EUR
    high = [c for c in claims if c["risk_level"] == "high"]
    assert all(c["exposure_eur"] == 200_000.0 for c in high)

    # report record exists and PDF was written
    assert report is not None
    assert report["pdf_path"] and report["pdf_path"].endswith(f"{scan['id']}.pdf")
    with open(report["pdf_path"], "rb") as f:
        assert f.read(5) == b"%PDF-"


def test_scan_error_path_marks_status(initialized_db, monkeypatch):
    from app.engine import crawler
    from app.database import _connect
    from app.services.scan_service import run_full_scan

    async def exploding_crawl(domain, max_pages):
        raise RuntimeError("network down")

    monkeypatch.setattr(crawler, "crawl_domain", exploding_crawl)

    async def run():
        scan_id = await _create_user_and_scan(initialized_db)
        await run_full_scan(scan_id)
        db = await _connect(initialized_db)
        try:
            cursor = await db.execute("SELECT status FROM scans WHERE id = ?", (scan_id,))
            (status,) = await cursor.fetchone()
        finally:
            await db.close()
        return status

    assert asyncio.run(run()) == "error"
