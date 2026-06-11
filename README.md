# Heron

**EmpCo (EU) 2024/825 compliance scanner for French e-commerce brands.**
Radar, pas juge.

Heron reads every product page of a storefront, flags each environmental
claim prohibited by Directive (EU) 2024/825 ("EmpCo"), prices the maximum
DGCCRF exposure per claim under Article L132-2 of the French Code de la
consommation, and delivers compliant replacement copy — ready to paste
into a CMS, with a timestamped PDF as a due-diligence trail.

## Repository layout

```
heron/
├── heron-backend/    Python / FastAPI API — see heron-backend/README.md
└── heron-frontend/   Next.js 14 frontend — see heron-frontend/README.md
```

## The one architectural rule

**Legal text never touches the LLM.**

- Detection is a deterministic regex engine. Same input, same output. No
  model decides what is a violation.
- Every article number and every statutory citation comes from the
  `legal_corpus` SQLite tables, which hold text **verbatim** from the
  Official Journal of the EU and Légifrance. Each article carries a
  `verification_status`; only `verified_source` text is ever reproduced
  in a report.
- Exposure amounts are exact arithmetic on the Article L132-2 formula
  (10% of average annual turnover, weighted by EmpCo severity), never
  estimated.
- Claude (Sonnet) does exactly one thing: it fills brand parameters into
  replacement templates written by a consumer-law specialist. It never
  generates, summarises or paraphrases legal text.

## What it does

| Capability | Where |
|---|---|
| Freemium homepage scan (no account, 1 claim visible) | `POST /api/v1/freemium/scan` |
| Full domain scan, 500–3 000 pages, background task | `POST /api/v1/scan` |
| Ads / email / social / transcript copy check (< 30 s, synchronous) | `POST /api/v1/ads/scan` |
| Embedded legal corpus, verbatim, publicly readable | `GET /api/v1/corpus` + `/legal` pages |
| Certificate upload (COSMOS, GOTS, GRS, FSC, EU Ecolabel, …) with automatic risk downgrade and audit trail | `/api/v1/evidence` |
| Timestamped PDF report with statutory source blocks | `GET /api/v1/report/{id}/pdf` |
| Admin: evidence review queue, scan browser, corpus reload | `/api/v1/admin/*` + `/dashboard/admin` |

## Quick start

Backend (Python 3.11+):

```bash
cd heron-backend
pip install -r requirements.txt
playwright install chromium          # browser for the crawler
cp .env.example .env                 # fill in keys
uvicorn main:app --port 8000
```

Frontend (Node 18+):

```bash
cd heron-frontend
npm install
cp .env.example .env.local
npm run dev                          # http://localhost:3000
```

Tests:

```bash
cd heron-backend && python -m pytest   # 106 tests
cd heron-frontend && npm run build     # type-checks all routes
```

## Legal corpus status

| Text | Status |
|---|---|
| Directive (EU) 2024/825 — Annex I pts 2a, 4a, 4b, 4c, 10a; Art. 6(2)(d) | ✅ verbatim, verified against OJ L 2024/825 |
| Code de la consommation — L. 121-2, L. 132-2 | ✅ verbatim, verified against Légifrance |
| Code de l'environnement — L. 541-9-4-1, R. 541-223 | ✅ verbatim, verified (Légifrance / Décret 2022-748) |
| Code de l'environnement — L. 541-9-1 | ⚠️ `pending_source` — excluded from reports until the verbatim Légifrance text is supplied |

To add or update a law: drop a JSON file in
`heron-backend/app/db/legal_corpus/`, reference it in `corpus_index.json`,
then `POST /api/v1/admin/corpus/reload` (or restart). No code change.

## Key dates

- **27 March 2026** — Member State transposition deadline (EmpCo Art. 4(1))
- **27 September 2026** — national measures apply; the prohibitions bite

---

Heron identifies. Your lawyer validates. *Radar, pas juge.*
