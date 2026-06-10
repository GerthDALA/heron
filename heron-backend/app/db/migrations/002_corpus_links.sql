-- Migration 002: legal corpus, evidence v2, ads scans.
-- For databases created with 001_initial.sql. Fresh databases get the
-- full schema from schema.sql and do not need this file.

-- Rules: corpus linkage
ALTER TABLE rules ADD COLUMN linked_article_ids TEXT;
ALTER TABLE rules ADD COLUMN source_corpus_id TEXT REFERENCES legal_corpus(id);

-- Claims: ads scan support. SQLite cannot drop NOT NULL on scan_id in
-- place, so rebuild the table.
ALTER TABLE claims ADD COLUMN ads_scan_id TEXT REFERENCES ads_scans(id);

CREATE TABLE claims_new (
    id TEXT PRIMARY KEY,
    scan_id TEXT REFERENCES scans(id),
    ads_scan_id TEXT REFERENCES ads_scans(id),
    rule_id TEXT NOT NULL,
    page_url TEXT NOT NULL,
    original_text TEXT NOT NULL,
    matched_pattern TEXT NOT NULL,
    empco_article TEXT NOT NULL,
    empco_article_full_ref TEXT NOT NULL,
    risk_level TEXT NOT NULL,
    exposure_eur REAL NOT NULL,
    replacement_text TEXT,
    replacement_generated INTEGER DEFAULT 0,
    is_visible_freemium INTEGER DEFAULT 0,
    created_at TEXT NOT NULL
);
INSERT INTO claims_new SELECT id, scan_id, ads_scan_id, rule_id, page_url,
    original_text, matched_pattern, empco_article, empco_article_full_ref,
    risk_level, exposure_eur, replacement_text, replacement_generated,
    is_visible_freemium, created_at FROM claims;
DROP TABLE claims;
ALTER TABLE claims_new RENAME TO claims;
CREATE INDEX IF NOT EXISTS idx_claims_scan_id ON claims(scan_id);
CREATE INDEX IF NOT EXISTS idx_claims_rule_id ON claims(rule_id);
CREATE INDEX IF NOT EXISTS idx_claims_ads_scan_id ON claims(ads_scan_id);

-- Evidence v2 replaces the original keyword-only table (no production data migrated).
DROP TABLE IF EXISTS evidence_records;

-- New tables (legal_corpus, legal_articles, rule_article_links,
-- certification_types, evidence_records v2, evidence_claim_links, ads_scans)
-- are created by re-running schema.sql, which is idempotent.
