from typing import Optional

from pydantic import BaseModel

from app.models.scan import Claim


class ReportLine(BaseModel):
    label: str
    value: str


class ReportSection(BaseModel):
    title: str
    lines: list[ReportLine] = []


class Report(BaseModel):
    id: str
    scan_id: str
    domain: str
    generated_at: Optional[str] = None
    pdf_path: Optional[str] = None
    download_count: int = 0
    total_claims: int = 0
    total_exposure_eur: float = 0
    claims: list[Claim] = []
