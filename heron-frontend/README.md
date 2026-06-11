# Heron Frontend

Next.js 14 (App Router, TypeScript strict) frontend for the Heron EmpCo
compliance scanner. Talks to the FastAPI backend in `../heron-backend`.

## Setup

```bash
npm install
cp .env.example .env.local   # NEXT_PUBLIC_API_URL + API_INTERNAL_URL
npm run dev                  # http://localhost:3000 (backend on :8000)
```

`npm run build` must pass with zero TypeScript errors before any merge.

## Stack

Tailwind CSS (Heron palette in `tailwind.config.ts`), Framer Motion,
Axios (typed client in `src/lib/api.ts`), React Hook Form + Zod,
Zustand (`src/store/`), Lucide icons, Inter + JetBrains Mono via
`next/font`.

## Pages

| Route | What |
|---|---|
| `/` | Marketing homepage (countdown, problem scenes, timeline, claims demo, pricing, FAQ, legal transparency) |
| `/scan`, `/scan/[id]` | Freemium homepage scan + results (1 claim visible, rest locked) |
| `/scan/ads`, `/scan/ads/[scanId]` | Freemium ads-copy check + results |
| `/legal`, `/legal/[corpusId]` | Public legal corpus — SSR, indexable, verbatim statutory text, never truncated |
| `/pricing` | Plans + ROI table |
| `/auth/login`, `/auth/register` | JWT auth |
| `/dashboard` | Scan history (`GET /scan`) + certificates widget |
| `/dashboard/new-scan` | Full scan with 3 s status polling |
| `/dashboard/report/[scanId]` | Full report, evidence-downgrade table, PDF download |
| `/dashboard/ads`, `/dashboard/ads/[scanId]` | Authenticated copy checks |
| `/dashboard/evidence`, `/dashboard/evidence/upload` | Certificate manager |
| `/dashboard/admin`, `/admin/scans`, `/admin/evidence` | Admin: stats, scan browser, certificate review queue, corpus reload (link appears only for `ADMIN_EMAILS` accounts) |

## Copy laws

Every user-facing string must be visualisable, falsifiable, and not
paste-able by a competitor. Banned words (powerful, seamless, robust,
plateforme, …) are listed in the project spec; check with:

```bash
grep -rinE "powerful|seamless|robust|innovative|plateforme" src/
```

Legal citations follow the verified OJ numbering — Annexe I points
4a / 4b / 4c and Article 6(2)(d) of Directive 2005/29/EC as amended by
Directive (EU) 2024/825 — matching what the backend returns.

## Deviations from the original UI spec

- shadcn/ui replaced by hand-built Tailwind primitives (small surface,
  no interactive CLI in the build environment).
- react-pdf omitted: PDFs are downloaded directly from the backend
  (spec constraint 6), never rendered client-side.
- FAQ answers 2–10 were written from product facts (the spec's source
  document was unavailable); Q1 is verbatim.
