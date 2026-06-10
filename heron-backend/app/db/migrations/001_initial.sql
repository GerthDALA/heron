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
    scan_id TEXT NOT NULL REFERENCES scans(id),
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
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS evidence_records (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(id),
    cert_type TEXT NOT NULL,      -- 'COSMOS', 'ECOCERT', 'FSC', 'EU_ECOLABEL', 'OTHER'
    cert_name TEXT NOT NULL,
    issuer TEXT NOT NULL,
    valid_until TEXT,
    covers_claims TEXT NOT NULL,  -- comma-separated pattern keywords it covers
    uploaded_at TEXT NOT NULL
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
