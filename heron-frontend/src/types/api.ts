export interface Claim {
  id: string;
  scan_id: string;
  rule_id: string;
  page_url: string;
  original_text: string;
  matched_pattern: string;
  empco_article: string;
  empco_article_full_ref: string;
  risk_level: "high" | "medium" | "low";
  exposure_eur: number;
  replacement_text: string | null;
  replacement_generated: boolean;
  is_visible_freemium: boolean;
  created_at: string;
}

export interface Scan {
  scan_id: string;
  status: "pending" | "running" | "complete" | "error";
  domain: string;
  total_claims: number;
  total_exposure_eur: number;
  pages_scanned: number;
  created_at: string;
  completed_at: string | null;
}

export interface FreemiumScanResult {
  scan_id: string;
  domain: string;
  visible_claims: Claim[];
  redacted_claims: Claim[];
  redacted_count: number;
  total_exposure_eur: number;
  cta_url: string;
}

export interface ScanListPage {
  scans: Scan[];
  total: number;
  page: number;
}

export interface Report {
  id: string;
  scan_id: string;
  domain: string;
  generated_at: string | null;
  pdf_path: string | null;
  download_count: number;
  total_claims: number;
  total_exposure_eur: number;
  claims: Claim[];
}

export interface LegalCorpus {
  id: string;
  short_name: string;
  full_name: string;
  jurisdiction: "EU" | "FR" | "DE";
  law_type?: string;
  official_reference?: string;
  publication_date?: string;
  application_date: string;
  status: "active" | "superseded" | "pending";
  article_count: number;
}

export interface LegalArticle {
  id: string;
  article_ref: string;
  article_title: string | null;
  full_text: string; // verbatim statutory text — display as-is
  summary: string;
  prohibited_behaviour: string;
  evidence_required: string | null;
  effective_from: string;
  verification_status: "verified_source" | "pending_source";
}

export interface CertificationType {
  id: string;
  name: string;
  issuer: string;
  jurisdiction?: string;
  covers_article: string;
  covers_claim_patterns?: string;
  description: string;
  iso_standard?: string | null;
  verification_url: string | null;
}

export interface EvidenceRecord {
  id: string;
  cert_type_id: string;
  cert_type_name: string;
  cert_number: string;
  cert_holder: string;
  issuer_name: string;
  issue_date: string;
  valid_until: string | null;
  scope: string;
  verified: 0 | 1 | 2;
  expires_soon: boolean;
  covers_article: string;
  covers_claim_patterns?: string;
  file_url: string | null;
}

export interface EvidenceSummary {
  active_certs: number;
  expiring_soon: number;
  covered_articles: string[];
}

export interface AdsScanResponse {
  scan_id: string;
  status: string;
  total_claims: number;
  total_exposure_eur: number;
  visible_claims: Claim[];
  redacted_claims: Claim[];
  redacted_count: number;
  is_freemium: boolean;
  note?: string | null;
}

export interface AdsScanDetail {
  scan: {
    id: string;
    input_type: string;
    input_title: string | null;
    status: string;
    total_claims: number;
    total_exposure_eur: number;
    is_freemium: number | boolean;
    created_at: string;
    completed_at: string | null;
  };
  claims: Claim[];
  redacted_count: number;
}

export interface AdminStats {
  users: number;
  scans: number;
  ads_scans: number;
  claims: number;
  evidence_records: number;
  evidence_pending_review: number;
  corpora: number;
  legal_articles: number;
  articles_pending_source: number;
  scans_by_status: Record<string, number>;
}

export interface AdminScanRow {
  id: string;
  user_id: string | null;
  user_email: string | null;
  domain?: string;
  input_title?: string | null;
  input_type?: string;
  status: string;
  total_claims: number;
  total_exposure_eur: number;
  is_freemium: number;
  created_at: string;
  completed_at: string | null;
}

export interface AdminEvidenceRow extends EvidenceRecord {
  user_email: string;
  verified_label: string;
  uploaded_at: string;
}
