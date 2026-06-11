from typing import Optional

import aiosqlite
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse

from app.api.deps import get_current_user, get_db
from app.services import evidence_service

router = APIRouter(prefix="/evidence", tags=["evidence"])


@router.get("/certification-types")
async def list_certification_types(db: aiosqlite.Connection = Depends(get_db)):
    cursor = await db.execute(
        "SELECT id, name, issuer, description, covers_article, iso_standard, "
        "verification_url FROM certification_types ORDER BY id"
    )
    return {"certification_types": [dict(row) for row in await cursor.fetchall()]}


@router.get("/summary")
async def evidence_summary(
    user: dict = Depends(get_current_user),
    db: aiosqlite.Connection = Depends(get_db),
):
    return await evidence_service.get_user_evidence_summary(user["id"], db)


@router.post("", status_code=201)
async def upload_evidence(
    cert_type_id: str = Form(...),
    cert_number: str = Form(...),
    cert_holder: str = Form(...),
    issuer_name: str = Form(...),
    issue_date: str = Form(...),
    valid_until: Optional[str] = Form(None),
    scope: str = Form(...),
    file: Optional[UploadFile] = File(None),
    user: dict = Depends(get_current_user),
    db: aiosqlite.Connection = Depends(get_db),
):
    file_bytes = await file.read() if file is not None else None
    try:
        record = await evidence_service.save_evidence(
            user_id=user["id"],
            form_data={
                "cert_type_id": cert_type_id,
                "cert_number": cert_number,
                "cert_holder": cert_holder,
                "issuer_name": issuer_name,
                "issue_date": issue_date,
                "valid_until": valid_until,
                "scope": scope,
            },
            file_bytes=file_bytes,
            file_name=file.filename if file is not None else None,
            content_type=file.content_type if file is not None else None,
            db=db,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    return {
        "evidence_id": record["id"],
        "cert_type": record["cert_type_id"],
        "verified": 0,
        "message": (
            "Certificat enregistré. Heron appliquera automatiquement la "
            "réduction de risque lors de vos prochains scans."
        ),
    }


@router.get("")
async def list_evidence(
    user: dict = Depends(get_current_user),
    db: aiosqlite.Connection = Depends(get_db),
):
    records = await evidence_service.list_user_evidence(user["id"], db)
    return {
        "evidence": [
            {
                "id": r["id"],
                "cert_type_id": r["cert_type_id"],
                "cert_type_name": r["cert_type_name"],
                "cert_number": r["cert_number"],
                "cert_holder": r["cert_holder"],
                "issuer_name": r["issuer_name"],
                "issue_date": r["issue_date"],
                "valid_until": r["valid_until"],
                "scope": r["scope"],
                "verified": r["verified"],
                "expires_soon": bool(r["expires_soon"]),
                "covers_article": r["covers_article"],
                "file_url": f"/api/v1/evidence/{r['id']}/file" if r["file_path"] else None,
            }
            for r in records
        ]
    }


@router.get("/{evidence_id}/file")
async def download_evidence_file(
    evidence_id: str,
    user: dict = Depends(get_current_user),
    db: aiosqlite.Connection = Depends(get_db),
):
    cursor = await db.execute(
        "SELECT file_path, file_original_name FROM evidence_records "
        "WHERE id = ? AND user_id = ?",
        (evidence_id, user["id"]),
    )
    row = await cursor.fetchone()
    if row is None or not row["file_path"]:
        raise HTTPException(status_code=404, detail="No file for this evidence record")
    return FileResponse(row["file_path"], filename=row["file_original_name"] or "certificate")


@router.delete("/{evidence_id}")
async def delete_evidence(
    evidence_id: str,
    user: dict = Depends(get_current_user),
    db: aiosqlite.Connection = Depends(get_db),
):
    deleted = await evidence_service.delete_evidence(user["id"], evidence_id, db)
    if not deleted:
        raise HTTPException(status_code=404, detail="Evidence not found")
    return {"deleted": True}
