"""Certificate validation and storage."""

import logging
import uuid
from datetime import date, datetime, timezone
from pathlib import Path

import aiosqlite

from app.config import get_settings
from app.services import email_service

logger = logging.getLogger("heron.evidence")

ALLOWED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png"}
ALLOWED_CONTENT_TYPES = {"application/pdf", "image/jpeg", "image/png"}

EXPIRES_SOON_SQL = """
    CASE WHEN valid_until IS NOT NULL
         AND julianday(valid_until) - julianday('now') < 60
    THEN 1 ELSE 0 END AS expires_soon
"""


def _parse_iso_date(value: str, field: str) -> str:
    try:
        return date.fromisoformat(value).isoformat()
    except ValueError:
        raise ValueError(f"{field} must be an ISO date (YYYY-MM-DD)")


async def save_evidence(
    user_id: str,
    form_data: dict,
    file_bytes: bytes | None,
    file_name: str | None,
    content_type: str | None,
    db: aiosqlite.Connection,
) -> dict:
    settings = get_settings()

    cursor = await db.execute(
        "SELECT * FROM certification_types WHERE id = ?", (form_data["cert_type_id"],)
    )
    cert_type = await cursor.fetchone()
    if cert_type is None:
        raise ValueError(f"Unknown cert_type_id: {form_data['cert_type_id']}")

    issue_date = _parse_iso_date(form_data["issue_date"], "issue_date")
    valid_until = None
    if form_data.get("valid_until"):
        valid_until = _parse_iso_date(form_data["valid_until"], "valid_until")

    evidence_id = str(uuid.uuid4())
    file_path = None

    if file_bytes is not None and file_name:
        ext = Path(file_name).suffix.lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise ValueError("File must be PDF or JPG/PNG")
        if content_type and content_type not in ALLOWED_CONTENT_TYPES:
            raise ValueError(f"Unsupported content type: {content_type}")
        # Content sniffing via libmagic when available; extension and
        # declared content type remain the fallback validation.
        try:
            import magic
            detected = magic.from_buffer(file_bytes[:4096], mime=True)
            if detected not in ALLOWED_CONTENT_TYPES:
                raise ValueError(f"File content is {detected}, expected PDF or JPG/PNG")
        except ImportError:
            logger.debug("python-magic unavailable — skipping content sniffing")
        if len(file_bytes) > settings.EVIDENCE_UPLOAD_MAX_MB * 1024 * 1024:
            raise ValueError(f"File exceeds {settings.EVIDENCE_UPLOAD_MAX_MB}MB limit")
        target_dir = Path(settings.EVIDENCE_STORAGE_PATH) / user_id
        target_dir.mkdir(parents=True, exist_ok=True)
        target = target_dir / f"{evidence_id}{ext}"
        try:
            import aiofiles
            async with aiofiles.open(target, "wb") as f:
                await f.write(file_bytes)
        except ImportError:
            target.write_bytes(file_bytes)
        file_path = str(target)

    record = {
        "id": evidence_id,
        "user_id": user_id,
        "cert_type_id": form_data["cert_type_id"],
        "cert_number": form_data["cert_number"],
        "cert_holder": form_data["cert_holder"],
        "issuer_name": form_data["issuer_name"],
        "issue_date": issue_date,
        "valid_until": valid_until,
        "scope": form_data["scope"],
        "file_path": file_path,
        "file_original_name": file_name,
        "verified": 0,
        "covers_claim_patterns": cert_type["covers_claim_patterns"],
        "uploaded_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.execute(
        """INSERT INTO evidence_records
           (id, user_id, cert_type_id, cert_number, cert_holder, issuer_name,
            issue_date, valid_until, scope, file_path, file_original_name,
            verified, covers_claim_patterns, uploaded_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            record["id"], record["user_id"], record["cert_type_id"],
            record["cert_number"], record["cert_holder"], record["issuer_name"],
            record["issue_date"], record["valid_until"], record["scope"],
            record["file_path"], record["file_original_name"], record["verified"],
            record["covers_claim_patterns"], record["uploaded_at"],
        ),
    )
    await db.commit()
    return record


async def list_user_evidence(user_id: str, db: aiosqlite.Connection) -> list[dict]:
    cursor = await db.execute(
        f"""SELECT e.*, ct.name AS cert_type_name, ct.covers_article,
                   {EXPIRES_SOON_SQL}
            FROM evidence_records e
            JOIN certification_types ct ON ct.id = e.cert_type_id
            WHERE e.user_id = ?
            ORDER BY e.uploaded_at DESC""",
        (user_id,),
    )
    return [dict(row) for row in await cursor.fetchall()]


async def delete_evidence(user_id: str, evidence_id: str, db: aiosqlite.Connection) -> bool:
    cursor = await db.execute(
        "SELECT * FROM evidence_records WHERE id = ? AND user_id = ?",
        (evidence_id, user_id),
    )
    record = await cursor.fetchone()
    if record is None:
        return False
    if record["file_path"]:
        Path(record["file_path"]).unlink(missing_ok=True)
    # evidence_claim_links rows are kept on purpose (audit trail)
    await db.execute("DELETE FROM evidence_records WHERE id = ?", (evidence_id,))
    await db.commit()
    return True


async def get_user_evidence_summary(user_id: str, db: aiosqlite.Connection) -> dict:
    records = await list_user_evidence(user_id, db)
    today = date.today().isoformat()
    active = [r for r in records if r["valid_until"] is None or r["valid_until"] > today]
    covered: set[str] = set()
    for r in active:
        covered.update(a.strip() for a in r["covers_article"].split(",") if a.strip())
    return {
        "active_certs": len(active),
        "expiring_soon": sum(1 for r in records if r["expires_soon"]),
        "covered_articles": sorted(covered),
    }


async def notify_expiring_certs(db: aiosqlite.Connection) -> int:
    """Email users whose certs expire within 60 days (max one notice / 30 days)."""
    cursor = await db.execute(
        f"""SELECT e.*, u.email AS user_email, ct.name AS cert_type_name,
                   {EXPIRES_SOON_SQL}
            FROM evidence_records e
            JOIN users u ON u.id = e.user_id
            JOIN certification_types ct ON ct.id = e.cert_type_id
            WHERE e.valid_until IS NOT NULL
              AND julianday(e.valid_until) - julianday('now') < 60
              AND (e.last_expiry_notice_at IS NULL
                   OR julianday('now') - julianday(e.last_expiry_notice_at) > 30)""",
    )
    rows = [dict(r) for r in await cursor.fetchall()]
    now = datetime.now(timezone.utc).isoformat()
    for row in rows:
        email_service._send(
            row["user_email"],
            f"Heron — votre certificat {row['cert_type_name']} expire bientôt",
            (
                f"Votre certificat {row['cert_type_name']} n°{row['cert_number']} "
                f"expire le {row['valid_until']}.\n\n"
                "Après expiration, Heron cessera d'appliquer la réduction de risque "
                "correspondante sur vos scans.\n\nHeron — Radar, pas juge."
            ),
        )
        await db.execute(
            "UPDATE evidence_records SET last_expiry_notice_at = ? WHERE id = ?",
            (now, row["id"]),
        )
        logger.info("Expiry notice sent for evidence %s", row["id"])
    await db.commit()
    return len(rows)
