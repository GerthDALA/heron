import uuid
from datetime import datetime, timezone

import aiosqlite
from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_db
from app.config import get_settings
from app.models.scan import Claim, FreemiumScanRequest, FreemiumScanResponse
from app.services import email_service, scan_service

router = APIRouter(prefix="/freemium", tags=["freemium"])


@router.post("/scan", response_model=FreemiumScanResponse)
async def freemium_scan(
    body: FreemiumScanRequest,
    db: aiosqlite.Connection = Depends(get_db),
):
    settings = get_settings()
    scan_id = str(uuid.uuid4())
    await db.execute(
        """INSERT INTO scans (id, user_id, domain, annual_revenue_eur, status, is_freemium, created_at)
           VALUES (?, NULL, ?, ?, 'pending', 1, ?)""",
        (scan_id, body.domain, body.annual_revenue_eur,
         datetime.now(timezone.utc).isoformat()),
    )
    await db.commit()

    try:
        claims = await scan_service.run_freemium_scan(
            db, scan_id, body.domain, body.annual_revenue_eur
        )
    except ValueError as exc:  # SSRF guard refused the target
        await db.execute("UPDATE scans SET status = 'error' WHERE id = ?", (scan_id,))
        await db.commit()
        raise HTTPException(status_code=422, detail=str(exc))
    total_exposure = round(sum(c["exposure_eur"] for c in claims), 2)
    visible = [c for c in claims if c["is_visible_freemium"]]
    redacted = [c for c in claims if not c["is_visible_freemium"]]
    redacted_count = len(redacted)

    def to_claim(c: dict, is_visible: bool) -> Claim:
        # Freemium never includes replacement text (paywall).
        return Claim(**{
            **{k: v for k, v in c.items() if k in Claim.model_fields},
            "replacement_text": None,
            "replacement_generated": False,
            "is_visible_freemium": is_visible,
        })

    visible_claims = [to_claim(c, True) for c in visible]
    redacted_claims = [to_claim(c, False) for c in redacted]

    email_service.send_freemium_report(body.email, {
        "domain": body.domain,
        "total_claims": len(claims),
        "total_exposure_eur": total_exposure,
        "visible_claims": [c.model_dump() for c in visible_claims],
        "redacted_count": redacted_count,
    })

    return FreemiumScanResponse(
        scan_id=scan_id,
        domain=body.domain,
        visible_claims=visible_claims,
        redacted_claims=redacted_claims,
        redacted_count=redacted_count,
        total_exposure_eur=total_exposure,
        cta_url=f"{settings.FRONTEND_URL}/checkout?scan_id={scan_id}",
    )
