# AGENTS.md — AI Agent Index

> Progressive disclosure guide for AI agents working in this repository.
> Start here, follow links to deeper docs as needed. Do not read every file — jump to the relevant section.

---

## What is this project?

**Hardware Deal Tracker** — A FastAPI + Next.js application that monitors eBay for deals on enterprise server hardware (AMD EPYC CPUs, workstation GPUs, ECC memory, NVMe storage, enterprise HDDs). It uses a tiered polling system to stay within eBay's 5,000 calls/day API limit, scores deals with a 6-component algorithm, and sends notifications via Telegram and email.

- **34 research-validated hardware items** in a curated catalog with scam floor detection
- **Tiered polling** across 4 priority tiers (P0 Hot 5min → P3 Passive 30min)
- **4-layer API rate limiting** to prevent overages
- **Mock eBay client** for development without real API credentials
- **Full Docker Compose stack**: PostgreSQL 17, Redis 7, FastAPI backend, Next.js 15 frontend, n8n

---

## Quick Orientation

| If you need to... | Read this |
|-------------------|-----------|
| Understand system architecture and data flow | [`agents/ARCHITECTURE.md`](agents/ARCHITECTURE.md) |
| Work on backend code (models, API, services) | [`agents/BACKEND.md`](agents/BACKEND.md) |
| Work on frontend code (pages, components, API calls) | [`agents/FRONTEND.md`](agents/FRONTEND.md) |
| Understand the database schema or write migrations | [`agents/DATABASE.md`](agents/DATABASE.md) |
| Set up local development or run tests | [`agents/DEVELOPMENT.md`](agents/DEVELOPMENT.md) |
| Work on eBay API integration or rate limiting | [`agents/EBAY_API.md`](agents/EBAY_API.md) |
| Understand or modify the deal scoring algorithm | [`agents/DEAL_SCORING.md`](agents/DEAL_SCORING.md) |
| Deploy to production or manage infrastructure | [`agents/DEPLOYMENT.md`](agents/DEPLOYMENT.md) |
| Add new hardware items to the catalog | [`agents/CATALOG.md`](agents/CATALOG.md) |

---

## Project Layout (30-second map)

```
project/
├── docker-compose.yml       # All services: postgres, redis, backend, frontend, n8n
├── .env.example             # Copy to .env, configure your credentials
├── Makefile                 # make up / make down / make migrate / make seed
├── backend/                 # FastAPI application (see agents/BACKEND.md)
│   ├── app/
│   │   ├── main.py          # App factory, CORS, router inclusion
│   │   ├── core/            # Settings (Pydantic), JWT security
│   │   ├── db/              # SQLAlchemy async engine + session
│   │   ├── models/          # 7 SQLAlchemy models
│   │   ├── schemas/         # Pydantic request/response schemas
│   │   ├── api/v1/endpoints/# 8 FastAPI router modules
│   │   └── services/        # eBay, scoring, notifications
│   ├── alembic/             # Database migrations
│   └── scripts/seed_data_v2.sql  # 34 validated items
└── frontend/                # Next.js 15 application (see agents/FRONTEND.md)
    ├── app/                 # App Router pages (dashboard, items, deals, etc.)
    ├── components/          # Shared React components
    └── lib/                 # API client + data hooks
```

---

## Golden Rules (read before editing anything)

1. **Never edit `docker-compose.yml` without checking `agents/DEPLOYMENT.md`** — service dependencies and health checks are carefully ordered.
2. **Always check `scam_floor` when modifying catalog items** — see [`agents/CATALOG.md`](agents/CATALOG.md).
3. **Frontend API calls go through `lib/api.ts`** — never hardcode API URLs in components.
4. **Backend settings are in `app/core/config.py`** — never hardcode values; use `settings.*`.
5. **Database changes need Alembic migrations** — see [`agents/DATABASE.md`](agents/DATABASE.md).
6. **eBay API calls must go through `RateBudgetManager`** — see [`agents/EBAY_API.md`](agents/EBAY_API.md).
7. **The `USE_MOCK_EBAY=true` env var enables the mock client** — safe for all development.

---

## Common Tasks (jump to the right doc)

| Task | Primary doc | Key files |
|------|------------|-----------|
| Add a new API endpoint | [`agents/BACKEND.md`](agents/BACKEND.md) | `api/v1/endpoints/*.py`, `api/v1/router.py`, `schemas/*.py` |
| Add a frontend page | [`agents/FRONTEND.md`](agents/FRONTEND.md) | `app/<route>/page.tsx`, `components/*.tsx`, `lib/api.ts` |
| Add a database table/column | [`agents/DATABASE.md`](agents/DATABASE.md) | `models/*.py`, `alembic/versions/`, `schemas/*.py` |
| Add a new tracked hardware item | [`agents/CATALOG.md`](agents/CATALOG.md) | `services/ebay/catalog.py`, `scripts/seed_data_v2.sql` |
| Change polling behavior | [`agents/EBAY_API.md`](agents/EBAY_API.md) | `services/ebay/poller.py`, `services/ebay/rate_budget.py` |
| Change deal scoring | [`agents/DEAL_SCORING.md`](agents/DEAL_SCORING.md) | `services/scoring/engine.py` |
| Add a notification channel | [`agents/BACKEND.md`](agents/BACKEND.md) | `services/notifications/*.py` |
| Run tests | [`agents/DEVELOPMENT.md`](agents/DEVELOPMENT.md) | `pytest`, `ruff` |
| Deploy | [`agents/DEPLOYMENT.md`](agents/DEPLOYMENT.md) | `docker-compose.yml`, `Makefile` |
