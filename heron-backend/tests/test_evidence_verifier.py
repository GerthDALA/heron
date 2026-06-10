"""Evidence downgrade logic tests."""

import asyncio
import uuid
from datetime import date, datetime, timedelta, timezone

import pytest

from app.engine.evidence_verifier import EvidenceVerifier


def _evidence(cert_type_id="COSMOS", covers_article="EMPCO_2024_825_ANNEX_4A",
              patterns="bio,biologique,organique,organic,naturel,natural,cosmos",
              cert_number="C-123", name="COSMOS Organic"):
    return {
        "id": str(uuid.uuid4()),
        "cert_type_id": cert_type_id,
        "cert_type_name": name,
        "cert_number": cert_number,
        "covers_article": covers_article,
        "covers_claim_patterns": patterns,
        "type_claim_patterns": patterns,
    }


verifier = EvidenceVerifier()

ARTICLES_4A = {"EMPCO_2024_825_ANNEX_4A"}
ARTICLES_4C = {"EMPCO_2024_825_ANNEX_4C", "EMPCO_2024_825_ART_6_2D"}


def test_cosmos_covers_biologique():
    assert verifier.matches_claim(_evidence(), "biologique", ARTICLES_4A)


def test_cosmos_does_not_cover_carbon_claim():
    # Different EmpCo article: COSMOS covers 4a, carbon claims sit under 4c/6(2)(d)
    assert not verifier.matches_claim(_evidence(), "carbon neutral by 2030", ARTICLES_4C)


def test_eu_ecolabel_covers_eco_friendly():
    ev = _evidence("EU_ECOLABEL", patterns="eco,ecological,environmentally friendly,ecolabel,respectueux,eco-friendly",
                   name="EU Ecolabel")
    assert verifier.matches_claim(ev, "eco-friendly", ARTICLES_4A)


def test_gots_covers_organic_cotton():
    ev = _evidence("GOTS", patterns="coton biologique,organic cotton,bio cotton", name="GOTS")
    assert verifier.matches_claim(ev, "organic cotton", ARTICLES_4A)


def test_grs_covers_recycled_polyester():
    ev = _evidence("GRS", patterns="recycled,recyclé,matière recyclée,recycled polyester", name="GRS")
    assert verifier.matches_claim(ev, "recycled polyester", ARTICLES_4A)


def test_keyword_match_alone_is_not_enough():
    # Keyword matches but the cert covers a different article → no downgrade
    ev = _evidence(covers_article="EMPCO_2024_825_ANNEX_4B")
    assert not verifier.matches_claim(ev, "biologique", ARTICLES_4A)


def test_downgraded_exposure_eu_ecolabel_is_ten_percent():
    assert verifier.calculate_downgraded_exposure(500_000, "EU_ECOLABEL") == 50_000.0
    assert verifier.calculate_downgraded_exposure(500_000, "ISO14024") == 50_000.0


def test_downgraded_exposure_cosmos_is_twenty_percent():
    for cert in ("COSMOS", "ECOCERT", "GOTS", "GRS", "FSC"):
        assert verifier.calculate_downgraded_exposure(500_000, cert) == 100_000.0


# --- Database-backed downgrade flow ---

async def _setup_user_with_cert(db_path, cert_type_id="COSMOS", valid_until=None):
    from app.database import _connect

    db = await _connect(db_path)
    user_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    await db.execute(
        "INSERT INTO users (id, email, password_hash, plan, created_at) "
        "VALUES (?, 'evidence@test.fr', 'x', 'starter', ?)",
        (user_id, now),
    )
    await db.execute(
        """INSERT INTO evidence_records
           (id, user_id, cert_type_id, cert_number, cert_holder, issuer_name,
            issue_date, valid_until, scope, verified, covers_claim_patterns, uploaded_at)
           VALUES (?, ?, ?, 'C-2024-001', 'Maison Test', 'Ecocert', '2024-01-01',
                   ?, 'gamme soins', 1, 'bio,biologique,naturel,natural,organic', ?)""",
        (str(uuid.uuid4()), user_id, cert_type_id, valid_until, now),
    )
    await db.commit()
    return db, user_id


async def _persist_one_claim(db, user_id, text="biologique", rule_id="VLX-EMP-001",
                             risk="high", exposure=500_000.0):
    scan_id = str(uuid.uuid4())
    claim_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    await db.execute(
        "INSERT INTO scans (id, user_id, domain, annual_revenue_eur, status, is_freemium, created_at) "
        "VALUES (?, ?, 'test.fr', 5000000, 'running', 0, ?)",
        (scan_id, user_id, now),
    )
    await db.execute(
        """INSERT INTO claims (id, scan_id, rule_id, page_url, original_text,
           matched_pattern, empco_article, empco_article_full_ref, risk_level,
           exposure_eur, created_at)
           VALUES (?, ?, ?, 'https://test.fr', ?, 'p', 'Annexe I, Point 4a', 'ref', ?, ?, ?)""",
        (claim_id, scan_id, rule_id, text, risk, exposure, now),
    )
    await db.commit()
    return {
        "id": claim_id, "scan_id": scan_id, "rule_id": rule_id,
        "original_text": text, "risk_level": risk, "exposure_eur": exposure,
    }


def test_apply_downgrades_full_flow(initialized_db):
    async def run():
        db, user_id = await _setup_user_with_cert(initialized_db)
        try:
            claim = await _persist_one_claim(db, user_id)
            claims = await EvidenceVerifier().apply_downgrades([claim], user_id, db)
            cursor = await db.execute(
                "SELECT * FROM evidence_claim_links WHERE claim_id = ?", (claim["id"],)
            )
            link = await cursor.fetchone()
            cursor = await db.execute(
                "SELECT risk_level, exposure_eur FROM claims WHERE id = ?", (claim["id"],)
            )
            row = await cursor.fetchone()
        finally:
            await db.close()
        return claims, dict(link) if link else None, dict(row)

    claims, link, row = asyncio.run(run())
    assert claims[0]["risk_level"] == "low"
    assert claims[0]["exposure_eur"] == 100_000.0  # COSMOS: 20% of 500k
    assert "COSMOS" in claims[0]["downgrade_note"]
    # Audit trail persisted
    assert link is not None
    assert link["original_risk_level"] == "high"
    assert link["downgraded_risk_level"] == "low"
    # Claim row updated in DB
    assert row["risk_level"] == "low"
    assert row["exposure_eur"] == 100_000.0


def test_expired_cert_not_applied(initialized_db):
    yesterday = (date.today() - timedelta(days=1)).isoformat()

    async def run():
        db, user_id = await _setup_user_with_cert(initialized_db, valid_until=yesterday)
        try:
            claim = await _persist_one_claim(db, user_id)
            claims = await EvidenceVerifier().apply_downgrades([claim], user_id, db)
        finally:
            await db.close()
        return claims

    claims = asyncio.run(run())
    assert claims[0]["risk_level"] == "high"
    assert claims[0]["exposure_eur"] == 500_000.0


def test_no_cert_no_downgrade(initialized_db):
    async def run():
        from app.database import _connect
        db = await _connect(initialized_db)
        user_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        await db.execute(
            "INSERT INTO users (id, email, password_hash, plan, created_at) "
            "VALUES (?, 'nocert@test.fr', 'x', 'starter', ?)",
            (user_id, now),
        )
        await db.commit()
        try:
            claim = await _persist_one_claim(db, user_id)
            claims = await EvidenceVerifier().apply_downgrades([claim], user_id, db)
        finally:
            await db.close()
        return claims

    claims = asyncio.run(run())
    assert claims[0]["risk_level"] == "high"
    assert claims[0]["exposure_eur"] == 500_000.0


def test_carbon_claim_not_downgraded_by_cosmos(initialized_db):
    async def run():
        db, user_id = await _setup_user_with_cert(initialized_db)
        try:
            claim = await _persist_one_claim(
                db, user_id, text="carbon neutral by 2030",
                rule_id="VLX-EMP-004",
            )
            claims = await EvidenceVerifier().apply_downgrades([claim], user_id, db)
        finally:
            await db.close()
        return claims

    claims = asyncio.run(run())
    assert claims[0]["risk_level"] == "high"


def test_downgrade_never_reduces_to_zero():
    assert verifier.calculate_downgraded_exposure(1_000, "EU_ECOLABEL") == 100.0
    assert verifier.calculate_downgraded_exposure(1_000, "COSMOS") == 200.0
