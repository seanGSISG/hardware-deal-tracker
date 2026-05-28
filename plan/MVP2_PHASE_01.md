# MVP2 Phase 01 — Make Data Flow

**Goal:** Listings ingested on a schedule, scored, visible in the dashboard. Real eBay API call succeeds end-to-end.

**Closes:** `G1` (poller scheduler), `B1` (eBay filter f-strings), `T1` partial (smoke tests for what we touch in this phase).

**Exit criterion:** With `USE_MOCK_EBAY=false` and valid credentials, a poll cycle inserts ≥1 real listing for at least 5 of the 34 tracked items, scores them, and they render in the dashboard. Smoke test suite (auth + health + scoring + one poller-with-mock test) is green.

---

## Dependencies

- T1.0 (scheduler decision) blocks T1.2, T1.3
- T1.1 (eBay f-string fix) blocks T1.4 (real-API smoke)
- T1.5 (test scaffold) blocks T1.6 (write actual tests)
- T1.2, T1.4, T1.6 can run in parallel once their blockers clear

---

## Tasks

### T1.0 — Scheduler decision ✅ (resolved 2026-05-27)

**Decision: APScheduler `AsyncIOScheduler` in-process.** Full rationale in [`.aidocs/decisions/scheduler.md`](../.aidocs/decisions/scheduler.md). T1.3 implements it.

---

### T1.1 — Fix eBay Browse client filter f-strings (B1)

**File:** `project/backend/app/services/ebay/client.py` (lines 78, 80, 83)

The doubled `{{ }}` are f-string escapes; the literal `{'|'.join(...)}` is sent to eBay. Pre-join the list outside the f-string:

```python
joined = "|".join(buying_options)
filters.append(f"buyingOptions:{{{joined}}}")
```

**Canonical fixture values** (from preflight research — see `MVP2_PREFLIGHT.md` §"eBay Browse API"):

| Input | Expected built string |
|-------|----------------------|
| `buying_options=["FIXED_PRICE", "AUCTION"]` | `buyingOptions:{FIXED_PRICE\|AUCTION}` |
| `condition_ids=["1000", "3000"]` | `conditionIds:{1000\|3000}` |
| `min_price=50, max_price=200` | `price:[50..200],priceCurrency:USD` |
| All three combined | comma-joined: `buyingOptions:{FIXED_PRICE\|AUCTION},conditionIds:{1000\|3000},price:[50..200],priceCurrency:USD` |

Also confirm `urllib.parse.urlencode({"filter": filter_string})` is used (or equivalent) — eBay needs `{`, `}`, `|`, `[`, `]`, `:`, `,` percent-encoded over the wire.

**Acceptance:** unit test in `tests/test_ebay_client.py` asserts the built filter string matches the fixtures above. No real API call required (the test inspects the built request, not the response).

---

### T1.2 — Wire `POST /search/trigger/{item_id}` and `/search/trigger-all` to the poller

**Files:** `project/backend/app/api/v1/endpoints/search.py`, `app/services/ebay/poller.py`

Replace the stub returns with actual calls to the poller. **Note actual signatures** (verified in preflight audit): `EbayPoller.search_item(db: AsyncSession, item: TrackedItem)` and `EbayPoller.search_all(db: AsyncSession)` — both take a db session; `search_item` takes the resolved `TrackedItem`, not just an id.

Endpoint pattern:

```python
@router.post("/trigger/{item_id}")
async def trigger_search(item_id: int, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    item = await db.get(TrackedItem, item_id)
    if not item:
        raise HTTPException(404)
    poller = EbayPoller()  # construct per existing convention — verify constructor args in poller.py
    return await poller.search_item(db, item)
```

Honor `RateBudgetManager` (don't trigger if the daily budget is exhausted; return 429 with `Retry-After`). The poller's existing logic already checks `RateBudgetManager.can_search()` — verify on read; if the endpoint should short-circuit before construction, add an explicit budget probe.

**Acceptance:** with mock client, `POST /search/trigger-all` inserts listings and returns a non-zero count. Smoke test covers this.

---

### T1.3 — Add APScheduler v3.11 and FastAPI lifespan, wire to poller

**Critical:** Pin `apscheduler>=3.11.2,<4`. APScheduler v4 is still **alpha** (latest 4.0.0a6, April 2025); the v4 API (`AsyncScheduler`, `add_schedule`, `start_in_background`) does NOT apply. Use the v3 API: `AsyncIOScheduler`, `add_job`, `start()`, `shutdown(wait=False)`.

**`app/main.py` has no `lifespan` currently** — T1.3 must *add* the `@asynccontextmanager async def lifespan(app: FastAPI)` and pass it to `FastAPI(lifespan=lifespan, ...)`. The original AGENTS doc references `@app.on_event("startup")`; do NOT use that (deprecated in FastAPI ≥0.109).

**Canonical pattern (preflight §"APScheduler"):**

```python
from contextlib import asynccontextmanager
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

scheduler = AsyncIOScheduler()

async def _poll_tick() -> None:
    async with AsyncSessionLocal() as db:
        await EbayPoller().search_all(db)  # adjust constructor per actual signature

@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings.SCHEDULER_ENABLED:
        scheduler.add_job(
            _poll_tick,
            IntervalTrigger(seconds=settings.POLL_SCHEDULER_INTERVAL),
            id="ebay-poll-tick",
            replace_existing=True,
            coalesce=True,        # collapse missed runs after downtime
            max_instances=1,      # never overlap
        )
        scheduler.start()
    yield
    if scheduler.running:
        scheduler.shutdown(wait=False)
```

**New env vars** (add to `app/core/config.py` + `.env.example`):
- `SCHEDULER_ENABLED: bool = True` (tests set `False`)
- `POLL_SCHEDULER_INTERVAL: int = 300` (seconds)

**Why `coalesce=True` + `max_instances=1`:** if the backend was down for 30 min, the scheduler will fire **one** catch-up tick instead of stacking N simultaneous ones; if a tick is still running when the next interval hits, the new tick is skipped (logged). Both prevent thundering-herd against Redis/DB and match the "tiered polling is an *opportunity*, not a guarantee" semantics.

The poller already iterates items in priority order and respects per-item `search_interval` — the scheduler just ticks; the poller decides which items are *due*.

**Acceptance:** docker compose up runs the backend, scheduler logs a "tick" line every interval, mock listings accumulate in `listings` table. SIGTERM (docker stop) returns cleanly within a few seconds.

---

### T1.4 — Real-API smoke (gated by credentials — ETA 2026-05-28)

**Status: blocked on creds landing.** Sean has eBay Browse API credentials arriving within 24h of plan creation (2026-05-27 → expected 2026-05-28). All other Phase 01 tasks can proceed in parallel against the mock client; T1.4 is the last step before phase exit.

Add a `pytest` marker `@pytest.mark.real_ebay` that's skipped unless `EBAY_CLIENT_ID` and `EBAY_CLIENT_SECRET` are set. One test: search for a single high-volume item (e.g. EPYC 7F72), assert ≥1 listing returned, assert it's persisted.

This is the test that proves T1.1's fix actually works against the live API. Run manually before declaring the phase complete; *not* required in CI.

**Acceptance:** running with real credentials returns listings.

---

### T1.5 — Test scaffold

`project/backend/tests/` **already exists** (preflight). `pyproject.toml [tool.pytest.ini_options]` already has `asyncio_mode = "auto"`. `make test` already invokes `docker compose exec backend pytest tests/ -xvs` correctly (DEFERRED_ISSUES G3 is overstated — the target works; it just had no tests to find).

Remaining scaffolding:
- `tests/conftest.py` — async test client fixture, isolated test DB (SQLite for speed, or a `tests_` schema in postgres via `DATABASE_URL` override), `SCHEDULER_ENABLED=False`, mock client always on
- `tests/__init__.py` (if not present)
- Register a `real_ebay` marker in `[tool.pytest.ini_options].markers` so `@pytest.mark.real_ebay` doesn't warn

**Acceptance:** `make test` runs and exits 0 (with zero tests, before T1.6 adds real ones).

---

### T1.6 — Smoke test suite (T1 subset)

Five tests, focused on what Phase 01 touches:

1. `test_health.py` — `GET /api/v1/health` returns 200
2. `test_auth.py` — register + login round trip returns a JWT that authorizes a `GET /items` call
3. `test_scoring.py` — feed `DealScoringEngine` known inputs, assert score components and total
4. `test_ebay_client.py` — built filter string matches fixture (validates B1 fix)
5. `test_poller.py` — with mock client, `EbayPoller.search_all()` inserts ≥1 listing per enabled item

The remaining T1 items (`test_rate_budget.py`, `test_catalog.py`) move to Phase 03.

**Acceptance:** all five tests green under `make test`.

---

## Verification (run all before declaring exit)

```bash
make test                                          # green
docker compose up -d                               # all healthy
curl -X POST localhost:8001/api/v1/search/trigger-all   # non-zero count
# wait one POLL_SCHEDULER_INTERVAL
# open dashboard at :3000 — listings visible
# with real eBay creds set:
USE_MOCK_EBAY=false pytest -m real_ebay            # green
```

Update `DEFERRED_ISSUES.md`: strike through G1, B1, and the five T1 items now covered.
