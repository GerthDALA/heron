from typing import Literal, Optional

from pydantic import BaseModel


class Rule(BaseModel):
    id: str
    version: str
    effective_date: str
    pattern: str
    language: Literal["fr", "en", "de"]
    risk_level: Literal["high", "medium", "low"]
    empco_article: str
    empco_article_full_ref: str
    legal_explanation: str
    safe_template: str
    requires_evidence: bool = False
    created_at: Optional[str] = None


class RuleMatch(BaseModel):
    rule_id: str
    matched_text: str
    context: str
    page_url: str
    empco_article: str
    empco_article_full_ref: str
    risk_level: Literal["high", "medium", "low"]
    legal_explanation: str
    safe_template: str


class EvidenceRecord(BaseModel):
    id: str
    user_id: str
    cert_type: Literal["COSMOS", "ECOCERT", "FSC", "EU_ECOLABEL", "OTHER"]
    cert_name: str
    issuer: str
    valid_until: Optional[str] = None
    covers_claims: str
    uploaded_at: str
