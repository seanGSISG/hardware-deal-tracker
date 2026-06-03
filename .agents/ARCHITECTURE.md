# Architecture Overview

> System-level view of how all components fit together. Read this before diving into backend or frontend specifics.

---

## Data Flow Diagram

```
User → Frontend (Next.js 3000) → Backend API (FastAPI 8000) → Services → External APIs
                                                              ↓
                                                        PostgreSQL / Redis
```

### Detailed Flow

```
1. POLLING LAYER (background, scheduled)
   ┌─────────────────────────────────────────────────────────────┐
   │  EbayPoller (async scheduler)                               │
   │  ├─ Runs every 60s, checks which items are due              │
   │  ├─ Groups items by priority tier (P0-P3)                   │
   │  ├─ Calls RateBudgetManager.can_search()                    │
   │  ├─ Calls EbayBrowseClient.search_item() or MockEbayClient  │
   │  ├─ Results → ListingParser.normalize()                     │
   │  ├─ DeduplicationEngine.filter_new()                        │
   │  ├─ DealScoringEngine.score()                               │
   │  ├─ New listings → DB (listings table)                      │
   │  └─ Price history → DB (price_history table)                │
   └─────────────────────────────────────────────────────────────┘

2. API LAYER (request/response)
   ┌─────────────────────────────────────────────────────────────┐
   │  Frontend → lib/api.ts → /api/v1/...                        │
   │  Auth: JWT bearer token (deps.py → security.py)             │
   │  Endpoints → SQLAlchemy queries → PostgreSQL                │
   │  Results → Pydantic schemas → JSON response                 │
   └─────────────────────────────────────────────────────────────┘

3. NOTIFICATION LAYER (event-driven)
   ┌─────────────────────────────────────────────────────────────┐
   │  Deal score ≥ threshold → TelegramClient.send_message()     │
   │  Deal score ≥ threshold → EmailClient.send_email()          │
   │  Alerts stored in alerts table for history                  │
   └─────────────────────────────────────────────────────────────┘

4. RATE LIMITING LAYER (pervasive)
   ┌─────────────────────────────────────────────────────────────┐
   │  Per-item: search_interval field on tracked_item            │
   │  Daily: Redis counter for total API calls                   │
   │  Near-limit: skip P3 → P2 → P1 items progressively          │
   │  Hard stop: halt all calls when within 200 of 5K limit      │
   └─────────────────────────────────────────────────────────────┘
```

---

## Service Boundaries

### Backend (`project/backend/app/`)

| Layer | Responsibility | Key Files |
|-------|---------------|-----------|
| **Core** | Configuration, auth, constants | `core/config.py`, `core/security.py` |
| **DB** | Connection management, base model | `db/base.py`, `db/session.py` |
| **Models** | SQLAlchemy ORM definitions | `models/*.py` (7 files) |
| **Schemas** | Pydantic validation for API I/O | `schemas/*.py` (5 files) |
| **API** | HTTP routing, request handling | `api/v1/endpoints/*.py` (8 files) |
| **Services** | Business logic, external integrations | `services/ebay/*.py`, `services/scoring/*.py`, `services/notifications/*.py` |

### Frontend (`project/frontend/`)

| Layer | Responsibility | Key Files |
|-------|---------------|-----------|
| **App Router** | Pages, layouts | `app/**/*.tsx` |
| **Components** | Shared React components | `components/*.tsx` |
| **Lib** | API client, data hooks | `lib/api.ts`, `lib/hooks.ts` |

---

## Key Architectural Decisions

### Why async everything?

The backend is fully async (FastAPI + SQLAlchemy async + asyncpg + httpx) because:
- The eBay poller makes many concurrent API calls
- Multiple tracked items are searched in parallel
- Long-running polling shouldn't block API requests

### Why Redis for rate limiting?

- Persistent daily counter survives backend restarts
- Atomic INCR operations prevent race conditions
- TTL on keys gives natural 24h window reset
- In-memory fallback when Redis is unavailable (degraded mode)

### Why a HardwareCatalog instead of free-form search?

- Prevents API waste on poorly-structured search keywords
- Enables scam_floor detection (requires known-good pricing)
- Provides benchmark_median for scoring calculations
- Gives users an auto-suggest "Add Item Wizard" experience

### Why separate MockEbayClient?

- eBay API credentials are not needed for development
- Generates realistic price variation for testing scoring
- Deterministic seed for reproducible test results
- Switchable at runtime via `USE_MOCK_EBAY` env var

---

## Request Lifecycle (typical API call)

```
1. Request hits FastAPI app (main.py)
   → CORS check (FRONTEND_URL whitelist)
   → URL routed to api/v1/router.py

2. Router delegates to endpoint module (e.g., items.py)
   → Auth dependency checks JWT (deps.py → security.py)
   → Request body validated by Pydantic schema

3. Endpoint queries database
   → Uses AsyncSession from db/session.py
   → SQLAlchemy model queries with async/await

4. Response serialized
   → SQLAlchemy model → Pydantic schema → JSON
   → HTTP response returned
```

## Polling Lifecycle (background process)

```
1. EbayPoller runs every 60 seconds (or on-demand via /search endpoint)

2. For each priority tier (P0 first, P3 last):
   a. Find items in this tier whose search_interval has elapsed
   b. For each due item:
      i.   RateBudgetManager.can_search()? → check Redis counter
      ii.  Get catalog entry for search keywords
      iii. Call EbayBrowseClient.search() or MockEbayClient
      iv.  Parse results via ListingParser
      v.   Filter duplicates via DeduplicationEngine
      vi.  Score new listings via DealScoringEngine
      vii. Save listings + scores to DB
      viii. Save price snapshots to price_history
      ix.  If score ≥ alert threshold → send notifications
      x.   Increment Redis API call counter

3. Sleep until next tick
```

---

## Environment-Driven Behavior

| Variable | When true/false | Behavior change |
|----------|-----------------|-----------------|
| `USE_MOCK_EBAY=true` | True | All eBay calls go to MockEbayClient |
| `USE_MOCK_EBAY=false` | False | Real eBay Browse API calls |
| Redis available | Connected | Full rate limiting, dedup caching |
| Redis unavailable | Connection fail | In-memory fallback, degraded rate tracking |
| `LOG_LEVEL=DEBUG` | Set | Verbose poller/scoring logs |
