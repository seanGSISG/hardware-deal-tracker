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

### T1.0 — Decide scheduler approach (no code)

**Output:** ADR-style note in `.aidocs/decisions/scheduler.md` (create directory). Decide between:
- **APScheduler** (in-process, simplest, sufficient for a single-backend homelab deployment)
- **n8n cron → `/search/trigger-all`** (uses already-running n8n, but n8n is currently unhealthy and slated for removal in Phase 03)
- **System cron + curl** (zero new dependencies, lives outside the container)

**Recommendation to consider:** APScheduler. Backend is the only process that needs the schedule; n8n is on death row; system cron means a host-side dependency that breaks the "docker compose up" story.

**Acceptance:** decision recorded with 2-3 sentence rationale. No code yet.

---

### T1.1 — Fix eBay Browse client filter f-strings (B1)

**File:** `project/backend/app/services/ebay/client.py` (lines 78, 80, 83)

The doubled `{{ }}` are f-string escapes; the literal `{'|'.join(...)}` is sent to eBay. Pre-join the list outside the f-string:

```python
joined = "|".join(buying_options)
filters.append(f"buyingOptions:{{{joined}}}")
```

**Acceptance:** unit test in `tests/test_ebay_client.py` asserts the built filter string matches a known-good fixture. No real API call required (the test inspects the built request, not the response).

---

### T1.2 — Wire `POST /search/trigger/{item_id}` and `/search/trigger-all` to the poller

**Files:** `project/backend/app/api/v1/endpoints/search.py`, `app/services/ebay/poller.py`

Replace the stub returns with actual calls to `EbayPoller.search_item(item_id)` and `search_all()`. Honor `RateBudgetManager` (don't trigger if the daily budget is exhausted; return 429 with `Retry-After`).

**Acceptance:** with mock client, `POST /search/trigger-all` inserts listings and returns a non-zero count. Smoke test covers this.

---

### T1.3 — Add APScheduler (or chosen scheduler) and wire to poller

Assuming T1.0 picks APScheduler:

- Add `apscheduler` to `pyproject.toml`
- In `app/main.py` lifespan, start an `AsyncIOScheduler` that calls `EbayPoller.search_all()` every N seconds (configurable via `POLL_SCHEDULER_INTERVAL`, default 300)
- The poller already iterates items in priority order and respects per-item `search_interval` — the scheduler just kicks the loop; the poller decides which items are *due*
- Add a `SCHEDULER_ENABLED` env flag (default `true`) so tests can disable it

**Acceptance:** docker compose up runs the backend, scheduler logs a "tick" line every interval, mock listings accumulate in `listings` table.

---

### T1.4 — Real-API smoke (gated by credentials)

Add a `pytest` marker `@pytest.mark.real_ebay` that's skipped unless `EBAY_CLIENT_ID` and `EBAY_CLIENT_SECRET` are set. One test: search for a single high-volume item (e.g. EPYC 7F72), assert ≥1 listing returned, assert it's persisted.

This is the test that proves T1.1's fix actually works against the live API. Run manually before declaring the phase complete; *not* required in CI.

**Acceptance:** running with real credentials returns listings.

---

### T1.5 — Test scaffold

Create `project/backend/tests/` with:
- `conftest.py` — async test client fixture, isolated test DB (SQLite or a `tests_` schema in postgres), `SCHEDULER_ENABLED=false`
- `pytest.ini` (or `pyproject.toml [tool.pytest.ini_options]`) — `asyncio_mode = auto`, `testpaths = tests`, markers registered

Wire `make test` to actually work (closes part of `G3`).

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
