"""Ads copy verification — synchronous text scans, no crawler."""

import uuid
from datetime import datetime, timezone
from typing import Literal, Optional

import aiosqlite
from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, EmailStr, Field, model_validator

from app.api.deps import get_db
from app.config import get_settings
from app.database import load_rules
from app.engine.ads_scanner import MAX_CHARS, MIN_CHARS, VALID_INPUT_TYPES, AdsScanner
from app.engine.evidence_verifier import EvidenceVerifier
from app.engine.regex_engine import RegexEngine
from app.engine.replacement_generator import ReplacementGenerator
from app.engine.report_builder import ReportBuilder
from app.engine.risk_calculator import RiskCalculator
from app.models.scan import Claim
from app.services import auth_service, email_service, scan_service

router = APIRouter(prefix="/ads", tags=["ads"])

_bearer = HTTPBearer(auto_error=False)


async def get_optional_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: aiosqlite.Connection = Depends(get_db),
) -> dict | None:
    if credentials is None:
        return None
    payload = auth_service.decode_token(credentials.credentials)
    if payload is None or "sub" not in payload:
        return None
    return await auth_service.get_user_by_id(db, payload["sub"])


class AdsScanRequest(BaseModel):
    input_type: Literal["ad_copy", "email", "social_post", "transcript", "other"]
    input_title: Optional[str] = None
    input_text: str = Field(min_length=MIN_CHARS, max_length=MAX_CHARS)
    annual_revenue_eur: float = Field(gt=0)
    email: Optional[EmailStr] = None

    @model_validator(mode="after")
    def transcript_note(self):
        return self


class AdsScanResponse(BaseModel):
    scan_id: str
    status: Literal["complete"] = "complete"
    total_claims: int
    total_exposure_eur: float
    visible_claims: list[Claim]
    redacted_count: int
    is_freemium: bool
    note: Optional[str] = None


TRANSCRIPT_NOTE = (
    "Transcripts are scanned as plain text only. Submit the speech text "
    "without timestamps or speaker labels (SRT/VTT formats are not parsed)."
)


def _row_to_claim(row: dict, redact_replacement: bool = False) -> Claim:
    data = {k: v for k, v in row.items() if k in Claim.model_fields}
    data["scan_id"] = row.get("scan_id") or row.get("ads_scan_id") or ""
    data["replacement_generated"] = bool(row.get("replacement_generated"))
    data["is_visible_freemium"] = bool(row.get("is_visible_freemium"))
    if redact_replacement:
        data["replacement_text"] = None
        data["replacement_generated"] = False
    return Claim(**data)


@router.post("/scan", response_model=AdsScanResponse)
async def create_ads_scan(
    body: AdsScanRequest,
    user: dict | None = Depends(get_optional_user),
    db: aiosqlite.Connection = Depends(get_db),
):
    settings = get_settings()
    is_freemium = user is None
    if is_freemium and not body.email:
        raise HTTPException(status_code=422, detail="email is required for freemium ads scans")

    scan_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    await db.execute(
        """INSERT INTO ads_scans
           (id, user_id, email, input_type, input_title, input_text, char_count,
            annual_revenue_eur, status, is_freemium, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'running', ?, ?)""",
        (scan_id, user["id"] if user else None, body.email, body.input_type,
         body.input_title, body.input_text, len(body.input_text),
         body.annual_revenue_eur, 1 if is_freemium else 0, now),
    )
    await db.commit()

    rules = await load_rules(db)
    scanner = AdsScanner(RegexEngine(rules), RiskCalculator())
    matches = scanner.scan_text(
        body.input_text, body.input_type, body.annual_revenue_eur,
        source_label=body.input_title or "submitted_text",
    )

    claims = await scan_service.persist_claims(
        db, matches, body.annual_revenue_eur,
        ads_scan_id=scan_id,
        freemium_visible=settings.FREEMIUM_MAX_CLAIMS_VISIBLE if is_freemium else 0,
    )

    if not is_freemium:
        claims = await EvidenceVerifier().apply_downgrades(claims, user["id"], db)
        if settings.ANTHROPIC_API_KEY and claims:
            generator = ReplacementGenerator(api_key=settings.ANTHROPIC_API_KEY)
            brand_context = {
                "domain": body.input_title or "ads copy",
                "industry": "e-commerce",
                "known_ingredients": "[à compléter]",
                "certifications": "aucune",
            }
            claims = await generator.generate_batch(claims, brand_context)
            for claim in claims:
                await db.execute(
                    "UPDATE claims SET replacement_text = ?, replacement_generated = 1 WHERE id = ?",
                    (claim.get("replacement_text"), claim["id"]),
                )
            await db.commit()

    total_exposure = round(sum(c["exposure_eur"] for c in claims), 2)
    await db.execute(
        """UPDATE ads_scans SET status = 'complete', total_claims = ?,
           total_exposure_eur = ?, completed_at = ? WHERE id = ?""",
        (len(claims), total_exposure, datetime.now(timezone.utc).isoformat(), scan_id),
    )
    await db.commit()

    if is_freemium:
        visible = [c for c in claims if c["is_visible_freemium"]]
        visible_claims = [_row_to_claim(c, redact_replacement=True) for c in visible]
        redacted = len(claims) - len(visible)
        email_service.send_freemium_report(body.email, {
            "domain": body.input_title or "votre copy publicitaire",
            "total_claims": len(claims),
            "total_exposure_eur": total_exposure,
            "visible_claims": [c.model_dump() for c in visible_claims],
            "redacted_count": redacted,
        })
    else:
        visible_claims = [_row_to_claim(c) for c in
                          sorted(claims, key=lambda c: c["exposure_eur"], reverse=True)]
        redacted = 0

    return AdsScanResponse(
        scan_id=scan_id,
        total_claims=len(claims),
        total_exposure_eur=total_exposure,
        visible_claims=visible_claims,
        redacted_count=redacted,
        is_freemium=is_freemium,
        note=TRANSCRIPT_NOTE if body.input_type == "transcript" else None,
    )


async def _load_ads_scan(scan_id: str, db: aiosqlite.Connection) -> dict:
    cursor = await db.execute("SELECT * FROM ads_scans WHERE id = ?", (scan_id,))
    scan = await cursor.fetchone()
    if scan is None:
        raise HTTPException(status_code=404, detail="Ads scan not found")
    return dict(scan)


async def _ads_claims(scan_id: str, db: aiosqlite.Connection) -> list[dict]:
    cursor = await db.execute(
        "SELECT * FROM claims WHERE ads_scan_id = ? ORDER BY exposure_eur DESC", (scan_id,)
    )
    return [dict(row) for row in await cursor.fetchall()]


@router.get("/scan/{scan_id}")
async def get_ads_scan(
    scan_id: str,
    email: Optional[str] = None,
    user: dict | None = Depends(get_optional_user),
    db: aiosqlite.Connection = Depends(get_db),
):
    scan = await _load_ads_scan(scan_id, db)
    owns = user is not None and scan["user_id"] == user["id"]
    freemium_match = scan["is_freemium"] and email and scan["email"] == email
    if not (owns or freemium_match):
        raise HTTPException(status_code=403, detail="Not authorised for this scan")
    claims = await _ads_claims(scan_id, db)
    redact = bool(scan["is_freemium"]) and not owns
    return {
        "scan": {k: scan[k] for k in ("id", "input_type", "input_title", "status",
                                      "total_claims", "total_exposure_eur",
                                      "is_freemium", "created_at", "completed_at")},
        "claims": [
            _row_to_claim(c, redact_replacement=redact).model_dump()
            for c in claims
            if not redact or c["is_visible_freemium"]
        ],
        "redacted_count": sum(1 for c in claims if redact and not c["is_visible_freemium"]),
    }


@router.get("/scan/{scan_id}/pdf")
async def get_ads_scan_pdf(
    scan_id: str,
    user: dict | None = Depends(get_optional_user),
    db: aiosqlite.Connection = Depends(get_db),
):
    if user is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    scan = await _load_ads_scan(scan_id, db)
    if scan["user_id"] != user["id"]:
        raise HTTPException(status_code=403, detail="You do not own this scan")
    claims = await _ads_claims(scan_id, db)
    exposure_summary = RiskCalculator().calculate_scan_exposure(
        claims, scan["annual_revenue_eur"]
    )
    pdf_scan = {
        "id": scan["id"],
        "domain": scan["input_title"] or "Copy publicitaire",
        "created_at": scan["created_at"],
        "total_exposure_eur": scan["total_exposure_eur"],
        "annual_revenue_eur": scan["annual_revenue_eur"],
    }
    pdf_bytes = ReportBuilder().build_report(
        pdf_scan, claims, exposure_summary, report_kind="ads"
    )
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="heron-ads-{scan_id}.pdf"'},
    )
