"""Admin surface: evidence verification queue, scan browsing, corpus reloads.

Access is gated by ADMIN_EMAILS — every route requires a JWT belonging to
a listed email. All actions here are operational; none of them touch the
verbatim statutory text itself (corpus content is only ever changed via the
JSON files + reload protocol).
"""

from typing import Literal, Optional

import aiosqlite
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.api.deps import get_admin_user, get_db
from app.database import check_corpus_updates, seed_corpus
from app.services import evidence_service

router = APIRouter(prefix="/admin", tags=["admin"])

VERIFIED_LABELS = {0: "unverified", 1: "user-attested", 2: "admin-verified"}


@router.get("/stats")
async def admin_stats(
    _admin: dict = Depends(get_admin_user),
    db: aiosqlite.Connection = Depends(get_db),
):
    stats = {}
    for key, query in {
        "users": "SELECT COUNT(*) FROM users",
        "scans": "SELECT COUNT(*) FROM scans",
        "ads_scans": "SELECT COUNT(*) FROM ads_scans",
        "claims": "SELECT COUNT(*) FROM claims",
        "evidence_records": "SELECT COUNT(*) FROM evidence_records",
        "evidence_pending_review": "SELECT COUNT(*) FROM evidence_records WHERE verified < 2",
        "corpora": "SELECT COUNT(*) FROM legal_corpus WHERE status = 'active'",
        "legal_articles": "SELECT COUNT(*) FROM legal_articles",
        "articles_pending_source": "SELECT COUNT(*) FROM legal_articles WHERE verification_status != 'verified_source'",
    }.items():
        cursor = await db.execute(query)
        (stats[key],) = await cursor.fetchone()
    cursor = await db.execute(
        "SELECT status, COUNT(*) AS n FROM scans GROUP BY status"
    )
    stats["scans_by_status"] = {row["status"]: row["n"] for row in await cursor.fetchall()}
    return stats


@router.get("/scans")
async def admin_list_scans(
    scan_type: Literal["domain", "ads"] = "domain",
    status: Optional[str] = None,
    page: int = 1,
    page_size: int = 50,
    _admin: dict = Depends(get_admin_user),
    db: aiosqlite.Connection = Depends(get_db),
):
    table = "scans" if scan_type == "domain" else "ads_scans"
    where = "WHERE s.status = ?" if status else ""
    params: list = [status] if status else []
    cursor = await db.execute(
        f"SELECT COUNT(*) FROM {table} s {where}", params
    )
    (total,) = await cursor.fetchone()
    cursor = await db.execute(
        f"""SELECT s.*, u.email AS user_email FROM {table} s
            LEFT JOIN users u ON u.id = s.user_id
            {where} ORDER BY s.created_at DESC LIMIT ? OFFSET ?""",
        params + [page_size, (page - 1) * page_size],
    )
    rows = [dict(row) for row in await cursor.fetchall()]
    for row in rows:
        row.pop("input_text", None)  # keep list payloads small for ads scans
    return {"scans": rows, "total": total, "page": page, "scan_type": scan_type}


@router.get("/evidence")
async def admin_evidence_queue(
    verified: Optional[int] = None,
    _admin: dict = Depends(get_admin_user),
    db: aiosqlite.Connection = Depends(get_db),
):
    where = "WHERE e.verified = ?" if verified is not None else ""
    params = [verified] if verified is not None else []
    cursor = await db.execute(
        f"""SELECT e.*, u.email AS user_email, ct.name AS cert_type_name,
                   {evidence_service.EXPIRES_SOON_SQL}
            FROM evidence_records e
            JOIN users u ON u.id = e.user_id
            JOIN certification_types ct ON ct.id = e.cert_type_id
            {where} ORDER BY e.uploaded_at ASC""",
        params,
    )
    rows = [dict(row) for row in await cursor.fetchall()]
    for row in rows:
        row["verified_label"] = VERIFIED_LABELS.get(row["verified"], "unknown")
    return {"evidence": rows, "total": len(rows)}


class VerifyEvidenceRequest(BaseModel):
    verified: Literal[0, 1, 2]
    note: Optional[str] = None


@router.post("/evidence/{evidence_id}/verify")
async def admin_verify_evidence(
    evidence_id: str,
    body: VerifyEvidenceRequest,
    admin: dict = Depends(get_admin_user),
    db: aiosqlite.Connection = Depends(get_db),
):
    cursor = await db.execute(
        "SELECT id, verified FROM evidence_records WHERE id = ?", (evidence_id,)
    )
    record = await cursor.fetchone()
    if record is None:
        raise HTTPException(status_code=404, detail="Evidence not found")
    await db.execute(
        "UPDATE evidence_records SET verified = ? WHERE id = ?",
        (body.verified, evidence_id),
    )
    await db.commit()
    return {
        "evidence_id": evidence_id,
        "previous": VERIFIED_LABELS[record["verified"]],
        "verified": body.verified,
        "verified_label": VERIFIED_LABELS[body.verified],
        "by": admin["email"],
    }


@router.post("/corpus/reload")
async def admin_reload_corpus(
    _admin: dict = Depends(get_admin_user),
    db: aiosqlite.Connection = Depends(get_db),
):
    """Re-read corpus JSON files from disk and upsert them — the API-side
    half of the update protocol (drop file + index entry, then reload)."""
    changed = await check_corpus_updates(db)
    corpora, articles = await seed_corpus(db)
    return {
        "changed_on_disk": changed,
        "corpora_loaded": corpora,
        "articles_loaded": articles,
    }


@router.post("/evidence/expiry-check")
async def admin_trigger_expiry_check(
    _admin: dict = Depends(get_admin_user),
    db: aiosqlite.Connection = Depends(get_db),
):
    sent = await evidence_service.notify_expiring_certs(db)
    return {"notices_sent": sent}
