# MVP2 Phase 03 — Data Quality + CI + Image Hygiene

**Goal:** Single source of truth for the catalog. Backend production image trimmed. `make seed` idempotent. CI green on every push. Decide n8n's fate.

**Closes:** `D1` (catalog/seed dedup), `D2` (benchmark price drift), `B2` (server_default audit), `B3` (priority_tier in list response), `B4` (n8n healthcheck — or removal), `I1` (compose version line), `I2` (multistage Dockerfile), `I5` (n8n pin — or removal), `I6` (frontend rebuild docs), `I7` (idempotent seed), `T2` (CI workflow), remaining `T1` items (`test_rate_budget.py`, `test_catalog.py`).

**Exit criterion:** `make test` runs in GitHub Actions on every push to `main` and every PR. Backend production image <300MB (currently ~50MB+ of dev deps). `make seed` re-runs cleanly on a populated DB. The 34 items match between `catalog.py` and `seed_data_v2.sql` (asserted by `test_catalog.py`). n8n is either healthy + pinned to a real version, or removed from the compose stack.

---

## Dependencies

- T3.0 (n8n decision) blocks T3.1 (either healthcheck fix or removal)
- T3.2 (catalog refactor) blocks T3.3 (catalog tests)
- All other tasks are independent

---

## Tasks

### T3.0 — n8n fate ✅ (resolved 2026-05-27)

**Decision: remove from compose stack.** Full rationale in [`.aidocs/decisions/n8n.md`](../.aidocs/decisions/n8n.md). T3.1 executes the removal.

---

### T3.1 — Remove n8n from the stack (closes B4, I5, DOC3)

- Delete `n8n` service block from `project/docker-compose.yml`
- Remove `n8n_data` (or equivalent) from the `volumes:` section
- Update `README.md` Tech Stack table and Features list — drop "n8n workflow engine"
- On docker-host-01: `cd ~/apps/hardware-deal-tracker && docker compose stop n8n && docker compose rm -f n8n && docker volume rm <volume-name>`

**Acceptance:** `docker compose ps` shows 4 healthy services (backend, frontend, postgres, redis); port 5678 free on docker-host-01.

---

### T3.2 — Catalog source-of-truth refactor (D1, D2)

**Files:** `project/backend/app/services/ebay/catalog.py`, `app/services/scoring/engine.py`, `scripts/seed_data_v2.sql`

The 34 items live in three places: Python `HardwareCatalog`, raw-SQL `seed_data_v2.sql`, and a `BENCHMARK_PRICES` dict in the scoring engine (preflight: 19 entries, several drift from catalog medians — e.g. `epyc 7f72: 350.0` vs catalog `benchmark_median=375`). Two changes:

1. **Drop `BENCHMARK_PRICES`** from `engine.py`. Always read benchmark from `tracked_item.benchmark_median` (already on the model). Scoring becomes a method that takes the `TrackedItem` object — **API change:** existing callers that pass listing text + score-by-keyword-match need to be updated to look up the `TrackedItem` first. The poller already has the `TrackedItem` in scope (see `EbayPoller.tick()` in `.agents/EBAY_API.md`), so this is a one-call-site change.
2. **Generate the SQL from the Python catalog.** Add `scripts/generate_seed.py` that reads `HardwareCatalog` and writes `seed_data_v2.sql`. Wire `make seed-regen` to run it. Keep the generated SQL committed (so deploys don't need Python at seed time) but treat `catalog.py` as the source of truth.

**Acceptance:** `python scripts/generate_seed.py` produces a file byte-identical to (or with deterministic diff against) the committed `seed_data_v2.sql`. `test_catalog.py` (T3.6) enforces this.

---

### T3.3 — Server-side defaults audit (B2)

**Files:** `project/backend/app/models/tracked_item.py`, `user.py`, and any other model with raw-SQL seeds

For every column with a Python-only `default=` that's also populated via raw SQL, add `server_default=...` and create an Alembic migration. Affected (at minimum):
- `tracked_items.alert_threshold`, `min_deal_score`, `is_enabled`, `search_interval`, `notification_settings`
- `users.is_active`
- `tracked_items.marketplace`

Make `seed_data_v2.sql` rely on the server defaults where possible (shorter, less drift surface).

**Acceptance:** Alembic migration generated and applied; raw-SQL `INSERT` with only required columns produces correct defaults.

---

### T3.4 — `priority_tier` in list response (B3)

**File:** `project/backend/app/api/v1/endpoints/items.py`

Add `response_model=ItemsListResponse` to `list_items`. Define `ItemsListResponse(BaseModel)` with `items: list[TrackedItemResponse]` (and whatever pagination/meta is already in the dict). `TrackedItemResponse` needs to include `priority_tier` as a computed field (Pydantic v2 `@computed_field`) so the property is serialized.

**Acceptance:** integration test asserts `GET /items` response has `priority_tier` on each item.

---

### T3.5 — Idempotent seed (I7)

**File:** `project/backend/scripts/seed_data_v2.sql`

Add `ON CONFLICT (name) DO NOTHING` to the `tracked_items` inserts (matching the existing `users` insert pattern). For columns that should *update* on re-seed (e.g. benchmark prices that we've adjusted), use `ON CONFLICT (name) DO UPDATE SET ...`.

**Acceptance:** `make seed` runs twice in a row without error; second run is a no-op or a controlled update.

---

### T3.6 — Remaining T1 tests

Two tests:
- `test_rate_budget.py` — verify `RateBudgetManager` enforces the 200-call buffer, the 4000-call priority skip threshold, and the 5000-call hard stop
- `test_catalog.py` — assert catalog has 34 items, every item has non-zero `scam_floor` where claimed, and `scripts/generate_seed.py` output matches the committed seed file (enforces T3.2)

**Acceptance:** both green under `make test`.

---

### T3.7 — Multistage backend Dockerfile (I2)

**File:** `project/backend/Dockerfile`

Two stages:
- `builder`: installs `[dev]` extras, used by CI for tests
- `runtime`: installs production deps only via `uv pip install --system .`

Backend prod image should drop pytest, ruff, pytest-asyncio, pytest-cov (~50MB+).

**Acceptance:** `docker image inspect hdt-backend --format='{{.Size}}'` is <300MB.

---

### T3.8 — Compose hygiene (I6 only — I1 struck)

**Preflight finding:** `project/docker-compose.yml` has **no `version:` line** (already absent). I1 is already done — strike it from the DEFERRED_ISSUES strike-through list with a one-line note ("no-op — line was already absent at audit time 2026-05-27").

**Files:** `project/Makefile`, `README.md`

- Update `Makefile` `up` target to invoke `docker compose build` first (so `NEXT_PUBLIC_*` env changes propagate)
- README: document the port-8001 remap and the `make build` requirement for frontend env changes

**Acceptance:** changing `NEXT_PUBLIC_API_URL` and running `make up` rebuilds and serves the new value.

---

### T3.9 — GitHub Actions CI (T2)

**New file:** `.github/workflows/ci.yml`

On push to `main` and on every PR:
- Set up Python via `astral-sh/setup-uv`
- `uv sync` (uses the committed `uv.lock`)
- Spin up postgres + redis as service containers
- Run `make test`
- Optionally: build the frontend (`npm ci && npm run build`) to catch type errors

**Acceptance:** workflow runs green on a test PR.

---

## Verification

```bash
make test                                          # green
docker image inspect project-backend --format='{{.Size}}'   # <300MB
make seed && make seed                             # both succeed
docker compose ps                                  # all healthy (no n8n if removed)
# push to a branch, open PR, CI green
```

Final pass on `DEFERRED_ISSUES.md`:
- Strike through everything closed across all 3 phases
- New section "Punted from MVP2" lists what remains (paperless? S1/S2? D3 category split? I9 passlib migration?)
- Update `~/command-center/.aidocs/repos/index.md` line for hardware-deal-tracker → "MVP2 complete"
- Final journal entry summarizing the three phases
