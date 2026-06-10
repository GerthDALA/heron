import uuid
from datetime import datetime, timezone

import aiosqlite
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException

from app.api.deps import get_current_user, get_db, get_owned_scan
from app.models.scan import Claim, ClaimsPage, ScanAccepted, ScanRequest, ScanResult
from app.services import scan_service

router = APIRouter(prefix="/scan", tags=["scan"])

PLAN_RANK = {"free": 0, "starter": 1, "brand": 2, "studio": 3}


@router.post("", response_model=ScanAccepted, status_code=202)
async def create_scan(
    body: ScanRequest,
    background_tasks: BackgroundTasks,
    user: dict = Depends(get_current_user),
    db: aiosqlite.Connection = Depends(get_db),
):
    if PLAN_RANK.get(user["plan"], 0) < PLAN_RANK[body.plan_tier]:
        raise HTTPException(
            status_code=403,
            detail=f"Your plan '{user['plan']}' does not allow '{body.plan_tier}' scans",
        )
    scan_id = str(uuid.uuid4())
    await db.execute(
        """INSERT INTO scans (id, user_id, domain, annual_revenue_eur, status, is_freemium, created_at)
           VALUES (?, ?, ?, ?, 'pending', 0, ?)""",
        (scan_id, user["id"], body.domain, body.annual_revenue_eur,
         datetime.now(timezone.utc).isoformat()),
    )
    await db.commit()
    background_tasks.add_task(scan_service.run_full_scan, scan_id)
    estimated = 120 if body.plan_tier == "starter" else 480
    return ScanAccepted(scan_id=scan_id, estimated_seconds=estimated)


@router.get("/{scan_id}", response_model=ScanResult)
async def get_scan(
    scan_id: str,
    user: dict = Depends(get_current_user),
    db: aiosqlite.Connection = Depends(get_db),
):
    scan = await get_owned_scan(scan_id, user, db)
    return ScanResult(
        scan_id=scan["id"],
        status=scan["status"],
        domain=scan["domain"],
        total_claims=scan["total_claims"],
        total_exposure_eur=scan["total_exposure_eur"],
        pages_scanned=scan["pages_scanned"],
        created_at=scan["created_at"],
        completed_at=scan["completed_at"],
    )


@router.get("/{scan_id}/claims", response_model=ClaimsPage)
async def get_scan_claims(
    scan_id: str,
    page: int = 1,
    page_size: int = 50,
    user: dict = Depends(get_current_user),
    db: aiosqlite.Connection = Depends(get_db),
):
    await get_owned_scan(scan_id, user, db)
    cursor = await db.execute("SELECT COUNT(*) FROM claims WHERE scan_id = ?", (scan_id,))
    (total,) = await cursor.fetchone()
    cursor = await db.execute(
        """SELECT * FROM claims WHERE scan_id = ?
           ORDER BY exposure_eur DESC LIMIT ? OFFSET ?""",
        (scan_id, page_size, (page - 1) * page_size),
    )
    rows = await cursor.fetchall()
    claims = [Claim(**{**dict(r),
                       "replacement_generated": bool(r["replacement_generated"]),
                       "is_visible_freemium": bool(r["is_visible_freemium"])})
              for r in rows]
    return ClaimsPage(claims=claims, total=total, page=page)
