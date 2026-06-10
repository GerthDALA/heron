"""Legal corpus loader.

Reads the structured legal corpus JSON files, validates them, and upserts
them into the legal_corpus / legal_articles tables. The full_text field is
verbatim statutory text: it is never modified, summarised, or paraphrased
by any part of the system — including the LLM, which never sees it.

Update protocol: drop a new JSON file into app/db/legal_corpus/, add an
entry to corpus_index.json, restart. No code change required.
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

import aiosqlite

logger = logging.getLogger("heron.corpus")

CORPUS_DIR = Path(__file__).resolve().parent.parent / "db" / "legal_corpus"
INDEX_PATH = CORPUS_DIR / "corpus_index.json"

REQUIRED_CORPUS_FIELDS = (
    "id", "short_name", "full_name", "jurisdiction", "law_type",
    "official_reference", "publication_date", "application_date", "status",
)
REQUIRED_ARTICLE_FIELDS = (
    "id", "article_ref", "full_text", "summary", "applies_to",
    "prohibited_behaviour", "effective_from",
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _parse_date(value: str) -> None:
    datetime.strptime(value, "%Y-%m-%d")


class CorpusLoader:
    def __init__(self, corpus_dir: Path | None = None):
        self.corpus_dir = corpus_dir or CORPUS_DIR
        self.index_path = self.corpus_dir / "corpus_index.json"

    def _read_index(self) -> dict:
        return json.loads(self.index_path.read_text(encoding="utf-8"))

    def _validate(self, data: dict) -> None:
        corpus = data["corpus"]
        for field in REQUIRED_CORPUS_FIELDS:
            if not corpus.get(field):
                raise ValueError(f"corpus missing field: {field}")
        _parse_date(corpus["publication_date"])
        _parse_date(corpus["application_date"])
        for article in data["articles"]:
            for field in REQUIRED_ARTICLE_FIELDS:
                if not article.get(field):
                    raise ValueError(f"article {article.get('id', '?')} missing field: {field}")
            _parse_date(article["effective_from"])

    async def load_all(self, db: aiosqlite.Connection) -> tuple[int, int]:
        """Upsert every active corpus from the index. Never raises on a bad
        file — logs the error and skips it. Returns (corpora, articles) loaded."""
        try:
            index = self._read_index()
        except Exception as exc:
            logger.error("Cannot read corpus_index.json: %s", exc)
            return (0, 0)

        corpora_loaded = articles_loaded = 0
        for entry in index.get("corpora", []):
            if entry.get("status") != "active":
                continue
            path = self.corpus_dir / entry["file"]
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                self._validate(data)
            except Exception as exc:
                logger.error("Skipping corpus file %s: %s", entry.get("file"), exc)
                continue

            corpus = data["corpus"]
            now = _now()
            await db.execute(
                """INSERT OR REPLACE INTO legal_corpus
                   (id, short_name, full_name, jurisdiction, law_type,
                    official_reference, publication_date, application_date,
                    status, superseded_by, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                           COALESCE((SELECT created_at FROM legal_corpus WHERE id = ?), ?), ?)""",
                (
                    corpus["id"], corpus["short_name"], corpus["full_name"],
                    corpus["jurisdiction"], corpus["law_type"],
                    corpus["official_reference"], corpus["publication_date"],
                    corpus["application_date"], corpus["status"],
                    corpus.get("superseded_by"), corpus["id"], now, now,
                ),
            )
            corpora_loaded += 1

            for article in data["articles"]:
                await db.execute(
                    """INSERT OR REPLACE INTO legal_articles
                       (id, corpus_id, article_ref, article_title, full_text,
                        summary, applies_to, prohibited_behaviour,
                        evidence_required, effective_from, verification_status,
                        created_at, updated_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                               COALESCE((SELECT created_at FROM legal_articles WHERE id = ?), ?), ?)""",
                    (
                        article["id"], corpus["id"], article["article_ref"],
                        article.get("article_title"), article["full_text"],
                        article["summary"], article["applies_to"],
                        article["prohibited_behaviour"],
                        article.get("evidence_required"),
                        article["effective_from"],
                        article.get("verification_status", "pending_source"),
                        article["id"], now, now,
                    ),
                )
                articles_loaded += 1
        await db.commit()
        logger.info("Loaded %d corpora, %d articles", corpora_loaded, articles_loaded)
        return (corpora_loaded, articles_loaded)

    async def get_article(self, article_id: str, db: aiosqlite.Connection) -> dict | None:
        cursor = await db.execute("SELECT * FROM legal_articles WHERE id = ?", (article_id,))
        row = await cursor.fetchone()
        return dict(row) if row else None

    async def get_articles_for_rule(self, rule_id: str, db: aiosqlite.Connection) -> list[dict]:
        cursor = await db.execute(
            """SELECT la.*, lc.full_name AS corpus_full_name
               FROM legal_articles la
               JOIN rule_article_links ral ON ral.article_id = la.id
               JOIN legal_corpus lc ON lc.id = la.corpus_id
               WHERE ral.rule_id = ?""",
            (rule_id,),
        )
        return [dict(row) for row in await cursor.fetchall()]

    async def get_corpus_summary(self, db: aiosqlite.Connection) -> list[dict]:
        cursor = await db.execute(
            """SELECT lc.id, lc.short_name, lc.full_name, lc.jurisdiction,
                      lc.law_type, lc.application_date, lc.status,
                      COUNT(la.id) AS article_count
               FROM legal_corpus lc
               LEFT JOIN legal_articles la ON la.corpus_id = lc.id
               WHERE lc.status = 'active'
               GROUP BY lc.id ORDER BY lc.id""",
        )
        return [dict(row) for row in await cursor.fetchall()]

    async def check_for_updates(self, db: aiosqlite.Connection) -> list[str]:
        """Return corpus IDs whose file on disk is newer than the DB record."""
        changed: list[str] = []
        try:
            index = self._read_index()
        except Exception as exc:
            logger.error("Cannot read corpus_index.json: %s", exc)
            return changed
        for entry in index.get("corpora", []):
            path = self.corpus_dir / entry["file"]
            if not path.exists():
                continue
            file_mtime = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
            cursor = await db.execute(
                "SELECT updated_at FROM legal_corpus WHERE id = ?", (entry["id"],)
            )
            row = await cursor.fetchone()
            if row is None:
                changed.append(entry["id"])
                continue
            db_updated = datetime.fromisoformat(row["updated_at"])
            if file_mtime > db_updated:
                changed.append(entry["id"])
        return changed
