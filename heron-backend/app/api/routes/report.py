from pathlib import Path

import aiosqlite
from fastapi import APIRouter, Depends, HTTPException, Response

from app.api.deps import get_current_user, get_db, get_owned_scan
from app.config import get_settings
from app.engine.report_builder import ReportBuilder
from app.engine.risk_calculator import RiskCalculator
from app.models.report import Report
from app.models.scan import Claim

router = APIRouter(prefix="/report", tags=["report"])


async def _scan_claims(db: aiosqlite.Connection, scan_id: str) -> list[dict]:
    cursor = await db.execute(
        "SELECT * FROM claims WHERE scan_id = ? ORDER BY exposure_eur DESC", (scan_id,)
    )
    return [dict(row) for row in await cursor.fetchall()]


@router.get("/{scan_id}", response_model=Report)
async def get_report(
    scan_id: str,
    user: dict = Depends(get_current_user),
    db: aiosqlite.Connection = Depends(get_db),
):
    scan = await get_owned_scan(scan_id, user, db)
    cursor = await db.execute("SELECT * FROM reports WHERE scan_id = ?", (scan_id,))
    report = await cursor.fetchone()
    claims = await _scan_claims(db, scan_id)
    return Report(
        id=report["id"] if report else "",
        scan_id=scan_id,
        domain=scan["domain"],
        generated_at=report["generated_at"] if report else None,
        pdf_path=report["pdf_path"] if report else None,
        download_count=report["download_count"] if report else 0,
        total_claims=scan["total_claims"],
        total_exposure_eur=scan["total_exposure_eur"],
        claims=[Claim(**{**c,
                         "replacement_generated": bool(c["replacement_generated"]),
                         "is_visible_freemium": bool(c["is_visible_freemium"])})
                for c in claims],
    )


@router.get("/{scan_id}/pdf")
async def get_report_pdf(
    scan_id: str,
    user: dict = Depends(get_current_user),
    db: aiosqlite.Connection = Depends(get_db),
):
    scan = await get_owned_scan(scan_id, user, db)
    if scan["status"] != "complete":
        raise HTTPException(status_code=409, detail=f"Scan status is '{scan['status']}'")

    claims = await _scan_claims(db, scan_id)
    exposure_summary = RiskCalculator().calculate_scan_exposure(
        claims, scan["annual_revenue_eur"]
    )
    pdf_bytes = ReportBuilder().build_report(scan, claims, exposure_summary)

    settings = get_settings()
    reports_dir = Path(settings.REPORTS_DIR)
    reports_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = reports_dir / f"{scan_id}.pdf"
    pdf_path.write_bytes(pdf_bytes)

    cursor = await db.execute("SELECT id FROM reports WHERE scan_id = ?", (scan_id,))
    report = await cursor.fetchone()
    if report:
        await db.execute(
            "UPDATE reports SET pdf_path = ?, download_count = download_count + 1 WHERE id = ?",
            (str(pdf_path), report["id"]),
        )
    else:
        import uuid
        from datetime import datetime, timezone
        await db.execute(
            "INSERT INTO reports (id, scan_id, pdf_path, generated_at, download_count) VALUES (?, ?, ?, ?, 1)",
            (str(uuid.uuid4()), scan_id, str(pdf_path), datetime.now(timezone.utc).isoformat()),
        )
    await db.commit()

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="heron-{scan_id}.pdf"'},
    )
