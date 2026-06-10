-- Heron SQLite schema

CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    plan TEXT NOT NULL DEFAULT 'free',    -- 'free', 'starter', 'brand', 'studio'
    created_at TEXT NOT NULL,
    stripe_customer_id TEXT
);

CREATE TABLE IF NOT EXISTS scans (
    id TEXT PRIMARY KEY,
    user_id TEXT REFERENCES users(id),
    domain TEXT NOT NULL,
    annual_revenue_eur REAL NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',  -- 'pending', 'running', 'complete', 'error'
    total_claims INTEGER DEFAULT 0,
    total_exposure_eur REAL DEFAULT 0,
    pages_scanned INTEGER DEFAULT 0,
    is_freemium INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    completed_at TEXT
);

CREATE TABLE IF NOT EXISTS claims (
    id TEXT PRIMARY KEY,
    scan_id TEXT REFERENCES scans(id),           -- NULL for ads scans
    ads_scan_id TEXT REFERENCES ads_scans(id),   -- NULL for domain scans; never both set
    rule_id TEXT NOT NULL,
    page_url TEXT NOT NULL,
    original_text TEXT NOT NULL,
    matched_pattern TEXT NOT NULL,
    empco_article TEXT NOT NULL,
    empco_article_full_ref TEXT NOT NULL,
    risk_level TEXT NOT NULL,            -- 'high', 'medium', 'low'
    exposure_eur REAL NOT NULL,
    replacement_text TEXT,
    replacement_generated INTEGER DEFAULT 0,
    is_visible_freemium INTEGER DEFAULT 0,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS rules (
    id TEXT PRIMARY KEY,          -- e.g. 'VLX-EMP-001'
    version TEXT NOT NULL,
    effective_date TEXT NOT NULL,
    pattern TEXT NOT NULL,        -- regex pattern string
    language TEXT NOT NULL DEFAULT 'fr',   -- 'fr', 'en', 'de'
    risk_level TEXT NOT NULL,     -- 'high', 'medium', 'low'
    empco_article TEXT NOT NULL,  -- e.g. 'Article 4a'
    empco_article_full_ref TEXT NOT NULL,  -- full citation
    legal_explanation TEXT NOT NULL,
    safe_template TEXT NOT NULL,  -- template with {brand_param} placeholders
    requires_evidence INTEGER DEFAULT 0,
    linked_article_ids TEXT,      -- comma-separated legal_articles IDs from corpus
    source_corpus_id TEXT REFERENCES legal_corpus(id),
    created_at TEXT NOT NULL
);

-- ─────────────────────────────────────────────
-- LEGAL CORPUS
-- ─────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS legal_corpus (
    id TEXT PRIMARY KEY,              -- e.g. 'EMPCO_2024_825'
    short_name TEXT NOT NULL,
    full_name TEXT NOT NULL,
    jurisdiction TEXT NOT NULL,       -- 'EU', 'FR', 'DE'
    law_type TEXT NOT NULL,           -- 'directive', 'code', 'regulation', 'decree'
    official_reference TEXT NOT NULL,
    publication_date TEXT NOT NULL,
    application_date TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'active',  -- 'active', 'superseded', 'pending'
    superseded_by TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS legal_articles (
    id TEXT PRIMARY KEY,              -- e.g. 'EMPCO_2024_825_ANNEX_4A'
    corpus_id TEXT NOT NULL REFERENCES legal_corpus(id),
    article_ref TEXT NOT NULL,        -- e.g. 'Annexe I, Point 4a'
    article_title TEXT,
    full_text TEXT NOT NULL,          -- verbatim statutory text — NEVER modified by LLM
    summary TEXT NOT NULL,            -- plain-language summary for UI display
    applies_to TEXT NOT NULL,         -- 'product_claims', 'brand_claims', 'ads', 'all'
    prohibited_behaviour TEXT NOT NULL,
    evidence_required TEXT,
    effective_from TEXT NOT NULL,
    verification_status TEXT NOT NULL DEFAULT 'pending_source',  -- 'verified_source', 'pending_source'
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

-- Link rules to their legal articles (one rule can cite multiple articles)
CREATE TABLE IF NOT EXISTS rule_article_links (
    rule_id TEXT NOT NULL REFERENCES rules(id),
    article_id TEXT NOT NULL REFERENCES legal_articles(id),
    PRIMARY KEY (rule_id, article_id)
);

-- ─────────────────────────────────────────────
-- EVIDENCE & CERTIFICATIONS
-- ─────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS certification_types (
    id TEXT PRIMARY KEY,              -- e.g. 'COSMOS', 'GOTS', 'EU_ECOLABEL'
    name TEXT NOT NULL,
    issuer TEXT NOT NULL,
    jurisdiction TEXT NOT NULL,       -- 'EU', 'FR', 'INTL'
    covers_article TEXT NOT NULL,     -- comma-separated article IDs this cert can satisfy
    covers_claim_patterns TEXT NOT NULL, -- comma-separated regex pattern keywords
    iso_standard TEXT,
    verification_url TEXT,
    description TEXT NOT NULL
);

-- User-uploaded certificates.
-- Note: 'expires_soon' is computed at query time (SQLite forbids
-- non-deterministic functions like julianday('now') in generated columns).
CREATE TABLE IF NOT EXISTS evidence_records (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(id),
    cert_type_id TEXT NOT NULL REFERENCES certification_types(id),
    cert_number TEXT NOT NULL,
    cert_holder TEXT NOT NULL,
    issuer_name TEXT NOT NULL,
    issue_date TEXT NOT NULL,
    valid_until TEXT,                 -- ISO date, NULL = no expiry
    scope TEXT NOT NULL,
    file_path TEXT,
    file_original_name TEXT,
    verified INTEGER NOT NULL DEFAULT 0,  -- 0=unverified, 1=user-attested, 2=admin-verified
    covers_claim_patterns TEXT NOT NULL,
    last_expiry_notice_at TEXT,
    uploaded_at TEXT NOT NULL
);

-- Audit trail: which cert downgraded which claim in which scan
CREATE TABLE IF NOT EXISTS evidence_claim_links (
    id TEXT PRIMARY KEY,
    claim_id TEXT NOT NULL REFERENCES claims(id),
    evidence_id TEXT NOT NULL REFERENCES evidence_records(id),
    original_risk_level TEXT NOT NULL,
    downgraded_risk_level TEXT NOT NULL,
    downgrade_reason TEXT NOT NULL,
    applied_at TEXT NOT NULL
);

-- ─────────────────────────────────────────────
-- ADS COPY SCANS
-- ─────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS ads_scans (
    id TEXT PRIMARY KEY,
    user_id TEXT REFERENCES users(id),   -- NULL for freemium
    email TEXT,                          -- freemium result delivery / retrieval
    input_type TEXT NOT NULL,            -- 'ad_copy', 'email', 'social_post', 'transcript', 'other'
    input_title TEXT,
    input_text TEXT NOT NULL,
    char_count INTEGER NOT NULL,
    annual_revenue_eur REAL NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    total_claims INTEGER DEFAULT 0,
    total_exposure_eur REAL DEFAULT 0,
    is_freemium INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    completed_at TEXT
);

CREATE TABLE IF NOT EXISTS reports (
    id TEXT PRIMARY KEY,
    scan_id TEXT NOT NULL REFERENCES scans(id) UNIQUE,
    pdf_path TEXT,
    generated_at TEXT,
    download_count INTEGER DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_claims_scan_id ON claims(scan_id);
CREATE INDEX IF NOT EXISTS idx_claims_rule_id ON claims(rule_id);
CREATE INDEX IF NOT EXISTS idx_scans_user_id ON scans(user_id);
CREATE INDEX IF NOT EXISTS idx_scans_domain ON scans(domain);
CREATE INDEX IF NOT EXISTS idx_evidence_user ON evidence_records(user_id);
CREATE INDEX IF NOT EXISTS idx_evidence_cert_type ON evidence_records(cert_type_id);
CREATE INDEX IF NOT EXISTS idx_ads_scans_user ON ads_scans(user_id);
CREATE INDEX IF NOT EXISTS idx_legal_articles_corpus ON legal_articles(corpus_id);
CREATE INDEX IF NOT EXISTS idx_rule_article_links_rule ON rule_article_links(rule_id);
CREATE INDEX IF NOT EXISTS idx_claims_ads_scan_id ON claims(ads_scan_id);
