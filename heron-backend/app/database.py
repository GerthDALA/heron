"""Async SQLite access via aiosqlite."""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import AsyncIterator

import aiosqlite

from app.config import get_settings

APP_DIR = Path(__file__).resolve().parent
SCHEMA_PATH = APP_DIR / "db" / "schema.sql"
RULES_SEED_PATH = APP_DIR / "db" / "rules_seed.json"
CERTIFICATIONS_SEED_PATH = APP_DIR / "db" / "certifications_seed.json"


def _db_path() -> str:
    return get_settings().sqlite_path


async def _connect(path: str | None = None) -> aiosqlite.Connection:
    db = await aiosqlite.connect(path or _db_path())
    db.row_factory = aiosqlite.Row
    await db.execute("PRAGMA foreign_keys = ON")
    # WAL lets readers proceed while a background scan writes; the busy
    # timeout makes concurrent writers wait instead of failing fast.
    await db.execute("PRAGMA journal_mode = WAL")
    await db.execute("PRAGMA busy_timeout = 5000")
    return db


async def get_db() -> AsyncIterator[aiosqlite.Connection]:
    """FastAPI dependency: yields an open connection, closes it afterwards."""
    db = await _connect()
    try:
        yield db
    finally:
        await db.close()


async def init_db(path: str | None = None) -> None:
    """Create all tables from schema.sql."""
    db = await _connect(path)
    try:
        await db.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
        await db.commit()
    finally:
        await db.close()


async def seed_rules(db: aiosqlite.Connection) -> int:
    """Insert rules from rules_seed.json if the rules table is empty.

    Returns the number of rules inserted.
    """
    cursor = await db.execute("SELECT COUNT(*) FROM rules")
    (count,) = await cursor.fetchone()
    if count > 0:
        return 0

    rules = json.loads(RULES_SEED_PATH.read_text(encoding="utf-8"))
    now = datetime.now(timezone.utc).isoformat()
    for rule in rules:
        await db.execute(
            """INSERT INTO rules
               (id, version, effective_date, pattern, language, risk_level,
                empco_article, empco_article_full_ref, legal_explanation,
                safe_template, requires_evidence, linked_article_ids,
                source_corpus_id, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                rule["id"],
                rule["version"],
                rule["effective_date"],
                rule["pattern"],
                rule["language"],
                rule["risk_level"],
                rule["empco_article"],
                rule["empco_article_full_ref"],
                rule["legal_explanation"],
                rule["safe_template"],
                rule.get("requires_evidence", 0),
                rule.get("linked_article_ids"),
                rule.get("source_corpus_id"),
                now,
            ),
        )
        for article_id in (rule.get("linked_article_ids") or "").split(","):
            article_id = article_id.strip()
            if article_id:
                await db.execute(
                    "INSERT OR IGNORE INTO rule_article_links (rule_id, article_id) VALUES (?, ?)",
                    (rule["id"], article_id),
                )
    await db.commit()
    return len(rules)


async def seed_corpus(db: aiosqlite.Connection) -> tuple[int, int]:
    """Load the legal corpus and certification types. Idempotent (upsert)."""
    from app.engine.corpus_loader import CorpusLoader

    counts = await CorpusLoader().load_all(db)

    certs = json.loads(CERTIFICATIONS_SEED_PATH.read_text(encoding="utf-8"))
    for cert in certs:
        await db.execute(
            """INSERT OR REPLACE INTO certification_types
               (id, name, issuer, jurisdiction, covers_article,
                covers_claim_patterns, iso_standard, verification_url, description)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                cert["id"], cert["name"], cert["issuer"], cert["jurisdiction"],
                cert["covers_article"], cert["covers_claim_patterns"],
                cert.get("iso_standard"), cert.get("verification_url"),
                cert["description"],
            ),
        )
    await db.commit()
    return counts


async def check_corpus_updates(db: aiosqlite.Connection) -> list[str]:
    """Reload any corpus whose file changed on disk since the last load."""
    from app.engine.corpus_loader import CorpusLoader

    loader = CorpusLoader()
    changed = await loader.check_for_updates(db)
    if changed:
        await loader.load_all(db)
        for corpus_id in changed:
            logging.getLogger("heron.corpus").info("Corpus %s updated — reloaded", corpus_id)
    return changed


async def load_rules(db: aiosqlite.Connection) -> list[dict]:
    cursor = await db.execute("SELECT * FROM rules")
    rows = await cursor.fetchall()
    return [dict(row) for row in rows]
