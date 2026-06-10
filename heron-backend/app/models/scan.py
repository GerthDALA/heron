from typing import Literal, Optional

from pydantic import BaseModel, EmailStr, Field


class ScanRequest(BaseModel):
    domain: str = Field(min_length=3)
    annual_revenue_eur: float = Field(gt=0)
    plan_tier: Literal["starter", "brand"] = "starter"


class FreemiumScanRequest(BaseModel):
    domain: str = Field(min_length=3)
    annual_revenue_eur: float = Field(gt=0)
    email: EmailStr


class Claim(BaseModel):
    id: str
    scan_id: str
    rule_id: str
    page_url: str
    original_text: str
    matched_pattern: str
    empco_article: str
    empco_article_full_ref: str
    risk_level: Literal["high", "medium", "low"]
    exposure_eur: float
    replacement_text: Optional[str] = None
    replacement_generated: bool = False
    is_visible_freemium: bool = False
    created_at: str


class ScanResult(BaseModel):
    scan_id: str
    status: Literal["pending", "running", "complete", "error"]
    domain: str
    total_claims: int = 0
    total_exposure_eur: float = 0
    pages_scanned: int = 0
    created_at: str
    completed_at: Optional[str] = None


class ScanAccepted(BaseModel):
    scan_id: str
    status: Literal["pending"] = "pending"
    estimated_seconds: int


class ClaimsPage(BaseModel):
    claims: list[Claim]
    total: int
    page: int


class FreemiumScanResponse(BaseModel):
    scan_id: str
    domain: str
    visible_claims: list[Claim]
    redacted_count: int
    total_exposure_eur: float
    cta_url: str
