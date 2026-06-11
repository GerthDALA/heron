# Heron Backend

FastAPI service implementing the Heron EmpCo compliance scanner: crawling,
deterministic claim detection, DGCCRF exposure pricing, certificate-based
risk downgrades, replacement generation via Claude, PDF reports, auth,
billing, and an admin surface.

## Stack

| Concern | Choice |
|---|---|
| Runtime | Python 3.11+, FastAPI, Uvicorn |
| Database | SQLite via `aiosqlite` (async everywhere) |
| Crawler | Crawl4AI + Playwright Chromium, stealth mode |
| Detection | `re` — compiled patterns from the `rules` table, zero LLM |
| LLM | Anthropic SDK, Claude Sonnet (`CLAUDE_MODEL`, default `claude-sonnet-4-5`) — template parameter filling only |
| PDF | ReportLab Platypus |
| Auth | JWT (python-jose) + bcrypt (passlib) |
| Billing | Stripe Checkout + webhook |
| Email | Resend (best-effort, never blocks a scan) |

## Setup

```bash
pip install -r requirements.txt
playwright install chromium
cp .env.example .env    # then fill in the keys below
uvicorn main:app --host 0.0.0.0 --port 8000
```

On startup the app creates the schema (`app/db/schema.sql`), loads the
legal corpus (`app/db/legal_corpus/`), seeds the certification types and
the 8 detection rules, and starts a daily certificate-expiry notifier.

### Environment variables (`.env`)

| Variable | Purpose |
|---|---|
| `ANTHROPIC_API_KEY` | Replacement generation. If empty, scans complete without replacements. |
| `CLAUDE_MODEL` | Model for template filling. Default `claude-sonnet-4-5`; switch to `claude-sonnet-4-6` (current Sonnet) when ready. |
| `STRIPE_SECRET_KEY` / `STRIPE_WEBHOOK_SECRET` | Checkout + webhook signature validation. |
| `RESEND_API_KEY` / `HERON_FROM_EMAIL` | Transactional email. Skipped if empty. |
| `JWT_SECRET_KEY` | Sign tokens. Change it. |
| `ADMIN_EMAILS` | JSON list, e.g. `["ops@brand.fr"]` — grants `/admin/*`. |
| `CRAWLER_ALLOW_PRIVATE_HOSTS` | SSRF guard override. Keep `false` in production; `true` only to scan a local mock storefront. |
| `MAX_PAGES_STARTER` / `MAX_PAGES_BRAND` | Crawl caps (500 / 3000). |
| `SCAN_TIMEOUT_SECONDS` / `FREEMIUM_TIMEOUT_SECONDS` | Crawl timeouts (600 / 120). |

## Architecture constraints (do not break these)

1. **`legal_articles.full_text` is verbatim statutory text.** It is loaded
   from the corpus JSON files, never edited via the API, never passed to
   the LLM, and only reproduced in reports when
   `verification_status = 'verified_source'`.
2. **Detection is deterministic.** `RegexEngine` compiles every rule at
   init and fails fast on a bad pattern. The ground truth lives in
   `tests/test_regex_engine.py` — extend it before touching a pattern.
3. **Exposure is exact.** `RiskCalculator`: `revenue × 0.10 × severity ×
   (0.2 if evidence)`. Severity: high 1.0 / medium 0.6 / low 0.3.
4. **Freemium never returns replacement text.** Visible and redacted
   claims both ship with `replacement_text: null`.
5. **Evidence downgrades, never dismisses.** A valid certificate reclasses
   a covered claim to `low` and multiplies exposure by 0.2 (0.1 for
   EU Ecolabel / ISO 14024). The claim stays in the report; the downgrade
   is audited in `evidence_claim_links`.

## Updating the law (zero code changes)

1. Write the new JSON in `app/db/legal_corpus/` (same shape as
   `empco_2024_825.json`); set `verification_status` honestly —
   `verified_source` only for verbatim text checked against the official
   PDF.
2. Add it to `corpus_index.json`.
3. `POST /api/v1/admin/corpus/reload` (or restart).

Rules cite corpus articles through `rule_article_links`; one rule can cite
several provisions (the carbon rules cite Annex I pt 4c **and**
Art. 6(2)(d)).

## API surface

```
GET    /api/v1/health
POST   /api/v1/auth/register | /auth/login
POST   /api/v1/freemium/scan                    # no auth, homepage only
POST   /api/v1/scan                             # background full scan
GET    /api/v1/scan                             # list own scans
GET    /api/v1/scan/{id} | /scan/{id}/claims
GET    /api/v1/report/{id} | /report/{id}/pdf
POST   /api/v1/ads/scan                         # synchronous text scan
GET    /api/v1/ads/scan/{id} | /ads/scan/{id}/pdf
GET    /api/v1/corpus | /corpus/{id} | /corpus/{id}/articles/{aid}   # public
GET    /api/v1/evidence | /evidence/summary | /evidence/certification-types
POST   /api/v1/evidence                         # multipart upload
GET    /api/v1/evidence/{id}/file
DELETE /api/v1/evidence/{id}
POST   /api/v1/billing/checkout | /billing/webhook
GET    /api/v1/admin/stats | /admin/scans | /admin/evidence          # ADMIN_EMAILS
POST   /api/v1/admin/evidence/{id}/verify | /admin/corpus/reload
POST   /api/v1/admin/evidence/expiry-check
```

## Tests

```bash
python -m pytest                 # 106 tests
python -m pytest -m slow         # + live crawl integration test
```

`tests/test_regex_engine.py` is the product contract: known prohibited
claims must match, documented compliant phrasings must not.

## Known limitations

- **SQLite**: single-writer. Fine for one instance; move to Postgres
  before horizontal scaling.
- **No rate limiting** on the unauthenticated endpoints — enforce at the
  reverse proxy before public launch.
- **Crawler depth**: product URLs are discovered from the homepage only
  (patterns `/produit`, `/product`, `/collection`, …); no recursive crawl.
- **Single long-lived JWT** (7 days); no refresh-token rotation.
- The stealth crawler does not honour `robots.txt` — a deliberate product
  decision to confirm before launch.
