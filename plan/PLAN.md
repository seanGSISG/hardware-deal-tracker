# Hardware Deal Tracker — Master Development Plan

## Project: AI-Powered Enterprise Hardware Deal Tracker
**Version:** 2.0  
**Date:** 2026-05-16  
**Architecture:** Self-hosted, Docker Compose, multi-service  
**Development Mode:** Parallel agentic swarm (Mode A)

---

## What's New in v2.0

- **34 tracked items** (up from 28) — validated pricing via 8 parallel research agents scanning eBay sold listings
- **New HDD 16TB+ category** — 6 drives for ZFS RAIDZ2 builds (Seagate Exos, WD Ultrastar, Toshiba MG)
- **Tiered polling system** — avoids eBay API 5K/day limit through configurable per-item intervals
- **Per-item interval control** in frontend — users set polling frequency per tracked item
- **Add Item wizard** — frontend form with eBay category picker, auto-suggest, and one-click add
- **Scam detection** — hard floor prices prevent false alerts on scam listings

---

## Executive Summary

This plan decomposes the Hardware Deal Tracker MVP into **9 parallel phases** across **bite-sized task files**, each targeting independent modules that can be developed simultaneously. The plan is designed for massive parallelization: up to **6 agents can work concurrently** during peak phases.

**Pricing validation complete:** All 34 tracked items have research-backed target prices derived from actual eBay sold listings (May 2026). See `research/PRICE_VALIDATION_REPORT.md`.

**Tracked items breakdown:**
- 1 CPU (EPYC 7F72)
- 2 motherboards (H12SSL-CT, ROMED8-2T)
- 3 workstation GPUs (RTX PRO 6000, RTX 6000 Ada, RTX PRO 4000 SFF)
- 2 inference GPUs (L4, T4)
- 5 ECC memory modules (Samsung ×2, Micron, Hynix ×2)
- 6 chassis/cooling/PSU/accessories
- 3 network adapters (ConnectX-4/5/6)
- 6 U.2 NVMe SSDs
- **6 HDDs 16TB+** (NEW — Exos X16/X18, Ultrastar HC550, MG08/MG09)

---

## Key Research Insights

| Finding | Impact on Plan |
|---------|---------------|
| eBay Finding API decommissioned Feb 2025 | Use Browse API exclusively; design for 5,000 calls/day limit |
| Browse API: 5K calls/day, 10K max results | **Tiered polling + per-item intervals keep usage under limit** |
| EPYC 7F72 median $375, ECC 64GB $145-240 | All benchmarks updated with real sold data |
| Enterprise SSDs hold value (P5510 $350+, PM9A3 $560+) | Scoring thresholds raised; scam floor detection added |
| 16TB used HDDs: $15-22/TB floor | New category with 6 drives for ZFS RAIDZ2 tracking |
| DDR4 ECC prices RISING (+10-20% Q4 2025) | Recommend immediate purchase for memory |
| Z-Score + weighted components = 97.1% precision | Hybrid scoring engine validated |

---

## Architecture Overview

```
Frontend (Next.js 15 + Tailwind + shadcn/ui)  [Port 3000]
       |
Backend (FastAPI + async SQLAlchemy 2.0 + Alembic)  [Port 8000]
       |
PostgreSQL 17 + pgvector (data + embeddings)  [Port 5432]
       |
n8n Workflow Engine (orchestration)  [Port 5678]
       |
Redis (caching + queues + rate limits)  [Port 6379]
       |
eBay Browse API (external data source)
OpenRouter AI (external AI inference)
Telegram Bot API (external notifications)
SMTP (external email delivery)
```

---

## API Limit Management (CRITICAL)

The 34-item configuration at default intervals exceeds eBay's 5,000 calls/day limit. The system implements **three layers of protection**:

### Layer 1: Tiered Polling Intervals

| Priority Tier | Items | Default Interval | Daily Calls | Examples |
|---------------|-------|-------------------|-------------|----------|
| **P0 Hot** | Active buys | 5 min | ~288 | EPYC 7F72, T4, ECC memory (5 items) |
| **P1 Standard** | Building soon | 10 min | ~144 | GPUs, motherboards, SSDs, HDDs (15 items) |
| **P2 Monitor** | Future buys | 20 min | ~72 | Chassis, PSU, cooler, accessories (10 items) |
| **P3 Passive** | Watch only | 30 min | ~48 | RTX PRO 6000 (too new), niche items (4 items) |
| **TOTAL** | **34 items** | **Weighted avg** | **~3,800** | **Under 5K limit** |

### Layer 2: Per-Item Interval Configuration

Every tracked item has a `search_interval` field (seconds). The frontend allows users to:
- Set custom intervals per item (60s minimum, 86400s maximum)
- Choose from preset tiers (Hot/Standard/Monitor/Passive)
- Temporarily pause items (disable without deleting)
- Bulk-edit intervals for multiple items

**API endpoint:** `PUT /api/v1/items/{id}` accepts `search_interval` in the body.

### Layer 3: Adaptive Rate Limiting (Backend)

```python
# In EbayPoller — checks global rate budget before each search
async def _check_rate_budget(self, db: AsyncSession) -> bool:
    """Check if we have API budget remaining. Skips low-priority items if near limit."""
    today_calls = await self._get_today_call_count(db)
    if today_calls >= 4800:  # 200 call buffer
        return False  # Skip this polling cycle
    elif today_calls >= 4000:
        # Near limit: only poll P0 items (skip P1/P2/P3)
        return item_priority == "P0"
    return True
```

**Frontend:** Dashboard shows real-time API usage bar (`today_calls / 5000`).

### Layer 4: Smart Scheduling

The poller queries items ordered by `last_searched + interval`, but with a priority multiplier:
- P0: no delay (search immediately when due)
- P1: +10s delay
- P2: +30s delay
- P3: +60s delay

This ensures hot items get searched first, and lower-priority items are gracefully deferred when near the limit.

---

## Frontend "Add Item" UX Specification

The frontend MUST make adding new tracked items effortless. This is a core workflow — users will add items regularly.

### Add Item Wizard (`/items/add` or modal)

**Step 1: Search / Auto-suggest**
```
[ Search for hardware to track...                     ]

Suggestions appear as user types (debounced 300ms):
  "RTX PRO 6000" → NVIDIA RTX PRO 6000 Blackwell 96GB
  "H12SSL" → Supermicro H12SSL-CT
  "Exos 16TB" → Seagate Exos X16 16TB
  "M393A8G40" → Samsung 64GB DDR4 ECC M393A8G40MB2-CVF

Each suggestion shows: name, category icon, current deal count, estimated price range
```

**Data source:** Pre-populated `catalog_items` table with 200+ common enterprise SKUs. The backend provides `GET /api/v1/catalog?q={query}` for auto-suggest. Users can also enter custom items not in the catalog.

**Step 2: Configure Item**
```
Selected: NVIDIA T4 16GB

Name:        [ NVIDIA T4 16GB                           ]
Keywords:    [ NVIDIA T4 16GB GPU inference accelerator  ]
eBay Category: [ Graphics/Video Cards (27386)         ▼ ]
Target Price:  [ $450.00                                ]
Alert Below:   [ 20% below median                    [?] ]
Priority:      (●) Hot (5 min)  ( ) Standard (10 min)  
                ( ) Monitor (20 min)  ( ) Custom: [___] min
Min Deal Score: [ 60 / 100                               ]
Enabled:       [✓] Active

Scam Floor:    $280 (auto-detected from benchmark data)
Est. Median:   $637 (from historical data if available)
```

**Step 3: Confirm**
```
✓ Item added! 34 items now tracked. ~108% → 92% of API budget.
[ View Item ]  [ Add Another ]  [ Go to Dashboard ]

⚠️ Budget impact: Adding 1 Hot item = +288 calls/day
                 Adding 1 Standard item = +144 calls/day
                 Adding 1 Monitor item = +72 calls/day
```

### Catalog System (Backend)

`backend/app/services/catalog.py` — Pre-loaded with ~200 enterprise hardware SKUs:

| Field | Purpose |
|-------|---------|
| `catalog_items` table | name, keywords, sku, mpn, category_id, benchmark_prices |
| `GET /api/v1/catalog?q=query` | Auto-suggest with fuzzy matching |
| `GET /api/v1/catalog/{id}` | Full item details + benchmark data |
| Benchmark prices | seed median, scam_floor from pricing research |

### Items List Page Features

The `/items` page MUST support:
1. **Table view** with sortable columns: name, target price, alert threshold, interval, deal count, status
2. **Interval editor** — inline dropdown per row (Hot/Standard/Monitor/Passive/Custom)
3. **Bulk actions** — select multiple items → change interval, enable, disable, or delete
4. **Priority badge** — color-coded row (red=P0 Hot, orange=P1, blue=P2, gray=P3)
5. **API budget impact** — footer bar showing `3,800 / 5,000 calls today` with items grouped by tier
6. **Search/filter** — by name, category, priority, enabled status
7. **Quick add** — "+" button on every row to clone item with same settings
8. **Import/Export** — CSV import for bulk item addition; JSON export for backup

---

## Phase Breakdown

| Phase | Module | Agent Count | Dependencies | Task File |
|-------|--------|-------------|--------------|-----------|
| 0 | Project Scaffold & Docker Compose | 1 | None | `PHASE_00.md` |
| 1 | Database Schema & Migrations | 1 | Phase 0 | `PHASE_01.md` |
| 2 | Backend Core (FastAPI + Auth + CRUD) | 1 | Phase 1 | `PHASE_02.md` |
| 3 | eBay Ingestion + Catalog + Rate Limiting | 1 | Phase 1 | `PHASE_03.md` |
| 4 | Deal Scoring Engine | 1 | Phase 1 | `PHASE_04.md` |
| 5 | Notification System (Telegram + Email) | 1 | Phase 1 | `PHASE_05.md` |
| 6 | Frontend Dashboard + Add Item UX | 2-3 | Phase 2 (API contracts) | `PHASE_06.md` |
| 7 | n8n Workflow Definitions | 1 | Phase 2+3+4+5 | `PHASE_07.md` |
| 8 | Docker Integration & Deployment | 1 | All above | `PHASE_08.md` |
| 9 | End-to-End Testing & QA | 1 | Phase 8 | `PHASE_09.md` |

---

## Parallel Execution Tracks

### Track A: Backend Core (Sequential within track)
```
Phase 0 (Scaffold) --> Phase 1 (DB) --> Phase 2 (API Core) 
                                              |
                                    Phase 3 (eBay + Catalog) --|
                                    Phase 4 (Scoring)         --|---> Phase 7 (n8n) --> Phase 8 (Deploy)
                                    Phase 5 (Alerts)          --|
```

### Track B: Frontend (Starts after API contracts defined)
```
Phase 2 complete (API contracts) --> Phase 6 (Frontend, 2-3 agents in parallel)
```

### Track C: Integration & Testing (Starts last)
```
All phases complete --> Phase 8 (Docker) --> Phase 9 (E2E Testing)
```

---

## Agent Allocation Strategy

### Round 1 (Max 4 parallel agents)
- Agent A: Phase 0 — Project scaffold + Docker Compose base
- Agent B: Phase 1 — Database schema + Alembic migrations
- *Phase 0 and Phase 1 can start together; Phase 1 just needs the directory structure*

### Round 2 (Max 6 parallel agents)
- Agent C: Phase 2 — Backend Core (needs Phase 1)
- Agent D: Phase 3 — eBay Ingestion + Catalog + Rate Limiting (needs Phase 1)
- Agent E: Phase 4 — Deal Scoring (needs Phase 1)
- Agent F: Phase 5 — Notifications (needs Phase 1)
- *These 4 can run in parallel once Phase 1 is complete*

### Round 3 (Max 3 parallel agents)
- Agent G: Phase 6a — Frontend scaffold + dashboard + Add Item wizard
- Agent H: Phase 6b — Frontend feature pages (items with intervals, deals, alerts, history)
- Agent I: Phase 7 — n8n workflow JSON definitions
- *These can run once Phase 2 API contracts are defined*

### Round 4 (1 agent)
- Agent J: Phase 8 + 9 — Integration, Docker finalization, testing

---

## Git Branching Strategy

```
main (shared repo at /mnt/agents/output/hardware-deal-tracker/project)
  ├── phase-00-scaffold      (Agent A)
  ├── phase-01-database      (Agent B)
  ├── phase-02-backend       (Agent C)
  ├── phase-03-ebay          (Agent D)
  ├── phase-04-scoring       (Agent E)
  ├── phase-05-notifications (Agent F)
  ├── phase-06-frontend      (Agent G - merged scaffold for H)
  ├── phase-07-n8n           (Agent I)
  └── phase-08-deploy        (Agent J)
```

**Merge order:**
1. Merge `phase-00-scaffold` → `main`
2. Merge `phase-01-database` → `main` (after scaffold)
3. Merge `phase-02` through `phase-05` in parallel → `main`
4. Merge `phase-06-frontend` → `main` (after phase-02)
5. Merge `phase-07-n8n` → `main` (after phase-02 through phase-05)
6. Merge `phase-08-deploy` → `main` (after all)

---

## Module Boundaries (for clean parallel development)

### Phase 2: Backend Core `/backend/app/`
- `main.py` — FastAPI app factory
- `core/config.py` — Pydantic settings
- `core/security.py` — JWT auth utilities
- `db/session.py` — Database session manager
- `models/` — SQLAlchemy ORM models
- `schemas/` — Pydantic request/response models
- `api/v1/endpoints/` — API route handlers
- `api/deps.py` — Dependencies (DB session, auth)

### Phase 3: eBay Ingestion `/backend/app/services/ebay/`
- `client.py` — Browse API client with rate limiting
- `parser.py` — Listing data normalization
- `poller.py` — Scheduled polling orchestrator with tiered intervals + rate budget
- `dedup.py` — Deduplication engine
- `mock.py` — Mock client for development
- `catalog.py` — Hardware catalog with 200+ SKUs + benchmark prices

### Phase 4: Deal Scoring `/backend/app/services/scoring/`
- `engine.py` — Rules-based scoring core with scam floor detection
- `historical.py` — Price history analytics
- `normalizer.py` — AI listing normalization (OpenRouter, post-MVP)
- `classifier.py` — Deal classification (OpenRouter, post-MVP)

### Phase 5: Notifications `/backend/app/services/notifications/`
- `telegram.py` — Telegram Bot API client
- `email.py` — SMTP email sender
- `templates.py` — Message templates
- `dispatcher.py` — Alert routing and batching

### Phase 6: Frontend `/frontend/`
- Next.js 15 + Tailwind + shadcn/ui
- App Router pattern
- `app/dashboard/` — Main dashboard with API usage bar
- `app/items/` — Tracked items CRUD with interval editor + Add Item wizard
- `app/items/add/` — Add Item wizard (auto-suggest → configure → confirm)
- `app/deals/` — Detected deals feed
- `app/alerts/` — Alert history and config
- `app/history/` — Price history charts
- `app/settings/` — Notification config

### Phase 7: n8n Workflows `/workflows/`
- `marketplace-poller.json` — eBay polling with tiered scheduling
- `deal-scorer.json` — Deal scoring trigger
- `notification-router.json` — Alert dispatch
- `daily-analytics.json` — Daily summary generation

---

## API Contract (Phase 2 Output → Phase 6 Input)

### Auth
```
POST   /api/v1/auth/register               # JWT login
POST   /api/v1/auth/login                  # JWT login
GET    /api/v1/me                           # Current user
```

### Tracked Items
```
GET    /api/v1/items                        # List tracked items (with ?priority=, ?enabled=, ?category=)
POST   /api/v1/items                        # Create tracked item (accepts search_interval)
GET    /api/v1/items/{id}                   # Get item detail
PUT    /api/v1/items/{id}                   # Update item (including search_interval)
PUT    /api/v1/items/{id}/toggle            # Quick enable/disable toggle
DELETE /api/v1/items/{id}                   # Delete item
POST   /api/v1/items/bulk-update            # Bulk update intervals/actions
GET    /api/v1/items/stats                  # API usage stats (calls_today, items_by_priority)
```

### Catalog (NEW — for Add Item auto-suggest)
```
GET    /api/v1/catalog?q={query}            # Auto-suggest hardware from catalog (fuzzy match)
GET    /api/v1/catalog/{id}                 # Full catalog item details
GET    /api/v1/categories                   # List eBay categories for picker
```

### Listings
```
GET    /api/v1/listings                     # List active listings (with ?item_id=)
GET    /api/v1/listings/{id}               # Get listing detail
```

### Price History
```
GET    /api/v1/history/{item_id}           # Price history
GET    /api/v1/history/stats/{item_id}     # Price statistics
```

### Deals
```
GET    /api/v1/deals                        # Get scored deals (with ?min_score=, ?item_id=)
GET    /api/v1/deals/{id}                   # Deal detail
```

### Alerts
```
GET    /api/v1/alerts                       # List alerts (with ?channel=, ?sent=)
PUT    /api/v1/alerts/{id}/read             # Mark alert read
```

### Settings
```
GET    /api/v1/settings/notifications       # Get notification config
PUT    /api/v1/settings/notifications       # Update notification config
```

### Search
```
POST   /api/v1/search/trigger/{item_id}    # Manual search trigger
POST   /api/v1/search/trigger-all          # Search all enabled items
```

---

## Environment Variables (`.env` contract)

```bash
# Database
DATABASE_URL=postgresql+asyncpg://postgres:postgres@postgres:5432/hardware_tracker

# Backend
SECRET_KEY=your-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
BACKEND_PORT=8000

# eBay API
EBAY_APP_ID=your-app-id
EBAY_CERT_ID=your-cert-id
EBAY_DEV_ID=your-dev-id
EBAY_REDIRECT_URI=your-redirect-uri

# OpenRouter AI
OPENROUTER_API_KEY=your-openrouter-key
OPENROUTER_MODEL=mistralai/mistral-small-3.1-24b-instruct

# Telegram
TELEGRAM_BOT_TOKEN=your-bot-token
TELEGRAM_CHAT_ID=your-chat-id

# Email
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email
SMTP_PASSWORD=your-app-password

# n8n
N8N_BASIC_AUTH_USER=admin
N8N_BASIC_AUTH_PASSWORD=admin-password
N8N_ENCRYPTION_KEY=your-encryption-key
WEBHOOK_URL=https://your-domain.com/

# Redis
REDIS_URL=redis://redis:6379/0

# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1

# Rate Limiting
EBAY_DAILY_CALL_LIMIT=5000        # eBay Browse API daily limit
EBAY_CALL_BUFFER=200              # Safety margin before hard stop
EBAY_NEAR_LIMIT_THRESHOLD=4000    # When to start skipping low-priority items
```

---

## Data Flow Architecture

```
Phase 3: eBay Poller (with tiered scheduling)
  ├── Every cycle: Query items ordered by (last_searched + interval × priority)
  ├── Before each call: Check global rate budget (Redis counter)
  ├── If near limit: Skip P1/P2/P3, only poll P0
  ├── If at limit: Skip cycle entirely
  ├── Store raw listings in `listings` table
  ├── Run deduplication against existing listings
  └── Trigger: webhook → Phase 4

Phase 4: Deal Scorer
  ├── On new listing: Check scam floor (from catalog benchmark)
  ├── If below scam floor: Flag as "suspicious", reduce score
  ├── Calculate base statistics
  ├── Apply rules-based scoring (price vs. history, seller, shipping)
  ├── Score 0-100 + confidence + classification
  ├── Store score in `listing_scores` table
  └── Trigger: webhook → Phase 5 (if score > threshold)

Phase 5: Notification Dispatcher
  ├── On high-score event: Build notification payload
  ├── Include scam warnings if score was suppressed
  ├── Route to Telegram (instant) or Email (digest)
  ├── Track sent alerts in `alerts` table
  └── Mark listing as notified

Phase 7: n8n Workflows
  ├── Workflow 1: Cron trigger → call Phase 3 with tiered scheduling
  ├── Workflow 2: Webhook trigger → call Phase 4
  ├── Workflow 3: Webhook trigger → call Phase 5
  └── Workflow 4: Cron trigger → daily analytics

Phase 6: Frontend
  ├── Dashboard: Real-time deals feed + API usage bar
  ├── Items: CRUD with per-item interval editor + priority badges
  ├── Add Item: Catalog auto-suggest → configure → confirm wizard
  ├── Alerts: Notification history + settings
  └── History: Charts from Phase 4 stats API
```

---

## Quality Gates

Each phase must pass before merge:

1. **Code compiles / builds** without errors
2. **Unit tests pass** (where applicable)
3. **Linter/formatter** clean (ruff for Python, ESLint for TypeScript)
4. **API contracts** match specification (if applicable)
5. **Integration points** documented (inputs, outputs, webhooks)
6. **Frontend UX** reviewed for Add Item flow and interval editing

---

## Phase Task Files

| File | Description |
|------|-------------|
| `PHASE_00.md` | Project scaffold, Docker Compose base, directory structure |
| `PHASE_01.md` | PostgreSQL schema (34 items + catalog), Alembic migrations, seed data |
| `PHASE_02.md` | FastAPI app, JWT auth, all CRUD endpoints + catalog API, tests |
| `PHASE_03.md` | eBay Browse API client, tiered poller, catalog service, rate limiting |
| `PHASE_04.md` | Deal scoring engine, scam floor detection, historical analytics |
| `PHASE_05.md` | Telegram bot, email SMTP, notification templates, dispatcher |
| `PHASE_06.md` | Next.js frontend, dashboard with API bar, Add Item wizard, interval editor |
| `PHASE_07.md` | n8n workflow JSONs for all 4 workflows |
| `PHASE_08.md` | Final Docker Compose, service integration, health checks |
| `PHASE_09.md` | End-to-end tests, smoke tests, documentation |

---

## Risk Mitigation

| Risk | Mitigation |
|------|-----------|
| eBay API rate limits (5K/day) | Tiered polling (P0-P3) + per-item intervals + adaptive rate limiter + Redis budget tracker |
| Browse API production approval | Design mock eBay client for development; swap to real API for staging |
| AI inference cost (OpenRouter) | Use cheapest capable model (Mistral Small 3.1); cache normalization results |
| Frontend/backend contract drift | API contracts defined in Phase 2, frozen before Phase 6 starts |
| Database schema changes | Alembic migrations; schema finalized in Phase 1 |
| Docker port conflicts | Document all ports; use `.env` overrides |
| Scam listings on eBay | Scam floor detection from catalog benchmark data; flag suspiciously low prices |

---

## Next Steps

1. **Read `REFINED_SPEC.md`** for the complete specification
2. **Review `research/PRICE_VALIDATION_REPORT.md`** for validated pricing data
3. **Dispatch Round 1 agents** for Phase 0 and Phase 1 (can start together)
4. **Wait for Phase 1 merge**, then dispatch Round 2 (Phases 2-5 in parallel)
5. **Wait for Phase 2 API contracts**, then dispatch Round 3 (Phase 6 + Phase 7 in parallel)
6. **Wait for all merges**, then dispatch Round 4 (Phase 8 + Phase 9)
