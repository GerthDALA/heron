"""Full scan pipeline orchestration.

Crawl → regex match → exposure calculation → evidence check →
replacement generation → report record + PDF → notification email.
Any failure flips the scan to 'error' and is logged; nothing crashes.
"""

import asyncio
import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path

import aiosqlite

from app.config import get_settings
from app.database import _connect, load_rules
from app.engine import crawler
from app.engine.corpus_loader import CorpusLoader
from app.engine.evidence_verifier import EvidenceVerifier
from app.engine.regex_engine import RegexEngine
from app.engine.replacement_generator import ReplacementGenerator
from app.engine.report_builder import ReportBuilder
from app.engine.risk_calculator import RiskCalculator
from app.services import email_service

logger = logging.getLogger("heron.scan")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


async def persist_claims(
    db: aiosqlite.Connection,
    matches: list[dict],
    annual_revenue_eur: float,
    scan_id: str | None = None,
    ads_scan_id: str | None = None,
    freemium_visible: int = 0,
) -> list[dict]:
    """Insert claim rows for each match, with exposure calculated per claim.

    Exactly one of scan_id / ads_scan_id must be set.
    """
    if bool(scan_id) == bool(ads_scan_id):
        raise ValueError("Exactly one of scan_id or ads_scan_id must be set")
    calculator = RiskCalculator()
    claims: list[dict] = []
    for index, match in enumerate(matches):
        exposure = match.get("exposure_eur") or calculator.calculate_claim_exposure(
            annual_revenue_eur, match["risk_level"]
        )
        claim = {
            "id": str(uuid.uuid4()),
            "scan_id": scan_id,
            "ads_scan_id": ads_scan_id,
            "rule_id": match["rule_id"],
            "page_url": match["page_url"],
            "original_text": match["matched_text"],
            "context": match.get("context", ""),
            "matched_pattern": match["matched_pattern"],
            "empco_article": match["empco_article"],
            "empco_article_full_ref": match["empco_article_full_ref"],
            "risk_level": match["risk_level"],
            "exposure_eur": exposure,
            "safe_template": match["safe_template"],
            "replacement_text": None,
            "is_visible_freemium": 1 if index < freemium_visible else 0,
            "created_at": _now(),
        }
        await db.execute(
            """INSERT INTO claims
               (id, scan_id, ads_scan_id, rule_id, page_url, original_text,
                matched_pattern, empco_article, empco_article_full_ref,
                risk_level, exposure_eur, replacement_text,
                replacement_generated, is_visible_freemium, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, 0, ?, ?)""",
            (
                claim["id"], scan_id, ads_scan_id, claim["rule_id"],
                claim["page_url"], claim["original_text"],
                claim["matched_pattern"], claim["empco_article"],
                claim["empco_article_full_ref"], claim["risk_level"],
                claim["exposure_eur"], claim["is_visible_freemium"],
                claim["created_at"],
            ),
        )
        claims.append(claim)
    await db.commit()
    return claims


async def articles_for_claims(db: aiosqlite.Connection, claims: list[dict]) -> dict[str, list[dict]]:
    """Map rule_id -> linked corpus articles, for report citations."""
    loader = CorpusLoader()
    result: dict[str, list[dict]] = {}
    for rule_id in {c["rule_id"] for c in claims}:
        result[rule_id] = await loader.get_articles_for_rule(rule_id, db)
    return result


async def run_full_scan(scan_id: str, db: aiosqlite.Connection | None = None) -> None:
    settings = get_settings()
    own_connection = db is None
    if own_connection:
        db = await _connect()
    try:
        cursor = await db.execute("SELECT * FROM scans WHERE id = ?", (scan_id,))
        scan = await cursor.fetchone()
        if scan is None:
            logger.error("Scan %s not found", scan_id)
            return
        scan = dict(scan)

        await db.execute("UPDATE scans SET status = 'running' WHERE id = ?", (scan_id,))
        await db.commit()

        rules = await load_rules(db)
        engine = RegexEngine(rules)

        cursor = await db.execute(
            "SELECT plan FROM users WHERE id = ?", (scan["user_id"],)
        )
        user_row = await cursor.fetchone()
        plan = user_row["plan"] if user_row else "starter"
        max_pages = settings.MAX_PAGES_BRAND if plan in ("brand", "studio") else settings.MAX_PAGES_STARTER

        pages = await asyncio.wait_for(
            crawler.crawl_domain(scan["domain"], max_pages),
            timeout=settings.SCAN_TIMEOUT_SECONDS,
        )
        await db.execute(
            "UPDATE scans SET pages_scanned = ? WHERE id = ?", (len(pages), scan_id)
        )
        await db.commit()

        matches = engine.match_all_pages(pages)
        claims = await persist_claims(
            db, matches, scan["annual_revenue_eur"], scan_id=scan_id
        )

        # Evidence downgrade: valid certificates reduce covered claims to 'low'
        claims = await EvidenceVerifier().apply_downgrades(claims, scan["user_id"], db)

        brand_context = {
            "domain": scan["domain"],
            "industry": "e-commerce",
            "known_ingredients": "[à compléter]",
            "certifications": "aucune",
        }
        if settings.ANTHROPIC_API_KEY and claims:
            generator = ReplacementGenerator(api_key=settings.ANTHROPIC_API_KEY)
            claims = await generator.generate_batch(claims, brand_context)
            for claim in claims:
                await db.execute(
                    "UPDATE claims SET replacement_text = ?, replacement_generated = 1 WHERE id = ?",
                    (claim.get("replacement_text"), claim["id"]),
                )
            await db.commit()

        total_exposure = round(sum(c["exposure_eur"] for c in claims), 2)
        completed_at = _now()
        await db.execute(
            """UPDATE scans SET status = 'complete', total_claims = ?,
               total_exposure_eur = ?, completed_at = ? WHERE id = ?""",
            (len(claims), total_exposure, completed_at, scan_id),
        )
        await db.commit()
        scan.update(
            total_claims=len(claims), total_exposure_eur=total_exposure,
            completed_at=completed_at,
        )

        report_id = str(uuid.uuid4())
        await db.execute(
            "INSERT OR REPLACE INTO reports (id, scan_id) VALUES (?, ?)",
            (report_id, scan_id),
        )
        await db.commit()

        calculator = RiskCalculator()
        exposure_summary = calculator.calculate_scan_exposure(
            claims, scan["annual_revenue_eur"]
        )
        articles_by_rule = await articles_for_claims(db, claims)
        pdf_bytes = ReportBuilder().build_report(
            scan, claims, exposure_summary, articles_by_rule=articles_by_rule
        )
        reports_dir = Path(settings.REPORTS_DIR)
        reports_dir.mkdir(parents=True, exist_ok=True)
        pdf_path = reports_dir / f"{scan_id}.pdf"
        pdf_path.write_bytes(pdf_bytes)
        await db.execute(
            "UPDATE reports SET pdf_path = ?, generated_at = ? WHERE id = ?",
            (str(pdf_path), _now(), report_id),
        )
        await db.commit()

        if scan["user_id"]:
            cursor = await db.execute(
                "SELECT email FROM users WHERE id = ?", (scan["user_id"],)
            )
            row = await cursor.fetchone()
            if row:
                email_service.send_scan_complete(
                    row["email"], scan_id, scan["domain"], len(claims), total_exposure
                )
    except Exception as exc:
        logger.exception("Scan %s failed: %s", scan_id, exc)
        try:
            await db.execute("UPDATE scans SET status = 'error' WHERE id = ?", (scan_id,))
            await db.commit()
        except Exception:
            logger.exception("Could not mark scan %s as error", scan_id)
    finally:
        if own_connection:
            await db.close()


async def run_freemium_scan(
    db: aiosqlite.Connection,
    scan_id: str,
    domain: str,
    annual_revenue_eur: float,
) -> list[dict]:
    """Homepage-only scan. No replacements (paywall). Returns persisted claims."""
    settings = get_settings()
    await db.execute("UPDATE scans SET status = 'running' WHERE id = ?", (scan_id,))
    await db.commit()

    rules = await load_rules(db)
    engine = RegexEngine(rules)
    try:
        page = await asyncio.wait_for(
            crawler.crawl_homepage(domain),
            timeout=settings.FREEMIUM_TIMEOUT_SECONDS,
        )
    except asyncio.TimeoutError:
        raise ValueError(
            f"Le scan de {domain} a dépassé {settings.FREEMIUM_TIMEOUT_SECONDS} secondes. "
            "Vérifiez que la page d'accueil répond et réessayez."
        )
    matches = engine.match_all_pages([page])

    claims = await persist_claims(
        db, matches, annual_revenue_eur, scan_id=scan_id,
        freemium_visible=settings.FREEMIUM_MAX_CLAIMS_VISIBLE,
    )
    total_exposure = round(sum(c["exposure_eur"] for c in claims), 2)
    await db.execute(
        """UPDATE scans SET status = 'complete', total_claims = ?,
           total_exposure_eur = ?, pages_scanned = 1, completed_at = ? WHERE id = ?""",
        (len(claims), total_exposure, _now(), scan_id),
    )
    await db.commit()
    return claims
