# Deferred Issues — Hardware Deal Tracker

After the first-build pass on 2026-05-15, the stack starts cleanly: `docker compose up -d` brings all services up, `alembic upgrade head` applies the schema, the seed inserts 34 items + admin, login + JWT works, all 13 API endpoints return 200 on the smoke test, and all 8 frontend routes render. The fixes that got us there are described in `/home/adminuser/.claude/plans/please-review-this-codebase-sunny-torvalds.md`.

This file lists everything that was **intentionally not fixed** during that pass — bugs that don't block the demo but should be addressed before this is treated as production. Items are grouped by severity and scope.

---

## Bugs (real, will misbehave under specific conditions)

### B1 — eBay Browse client filter strings are broken f-strings
**File:** `project/backend/app/services/ebay/client.py:78,80,83`
**Symptom:** When `USE_MOCK_EBAY=false`, the real eBay client builds filter parameters like `f"buyingOptions:{{'|'.join(buying_options)}}"`. The doubled `{{ }}` are f-string escapes for literal braces, so the literal text `{'|'.join(buying_options)}` is sent to eBay → 400 Bad Request from the filter parser. The `|`.join() call is never executed.
**Impact:** Mock client masks this in dev. Will block the first real-API switch.
**Fix:** Use single braces and pre-join the list, e.g. `joined = "|".join(buying_options); filters.append(f"buyingOptions:{{{joined}}}")` (or just build the string outside the f-string).

### B2 — Python-level model defaults don't apply to raw-SQL seeds
**Files:** `project/backend/app/models/user.py`, `models/tracked_item.py`
**Symptom:** Discovered during this pass for `users.is_active` and `tracked_items.marketplace`. SQLAlchemy `default=True` / `default="ebay"` runs only when inserting via the ORM. The raw-SQL `INSERT` statements in `seed_data_v2.sql` left those columns NULL, which broke `get_current_user` (NULL is_active fails the `not user.is_active` check) and `/items/{id}` (NULL marketplace failed the Pydantic `str` validation in `TrackedItemResponse`).
**Workaround applied:** patched the seed file to include both columns explicitly + ran `UPDATE` on the live DB.
**Proper fix:** add `server_default` to the model columns and create a migration so the database itself enforces the defaults. Audit every other column with a Python-only `default=` — at minimum `tracked_items.alert_threshold`, `min_deal_score`, `is_enabled`, `search_interval`, and `notification_settings` defaults are also affected if anyone seeds those tables via raw SQL later.

### B3 — `GET /items` list response omits `priority_tier`
**File:** `project/backend/app/api/v1/endpoints/items.py:43-48`
**Symptom:** `list_items` returns the raw SQLAlchemy rows in a dict (`{"items": items, ...}`) without a `response_model`. FastAPI's default serialization doesn't read `@property`-typed fields, so the `priority_tier` property defined on `TrackedItem` is silently dropped from list responses (single-item GET works because it has `response_model=TrackedItemResponse`).
**Impact:** Frontend recomputes the badge from `search_interval` so the UI works, but any consumer relying on the field will see it missing.
**Fix:** Add `response_model=ItemsListResponse` (define a Pydantic wrapper that holds `items: list[TrackedItemResponse]`).

### B4 — `n8n` container is unhealthy (cosmetic)
**File:** `project/docker-compose.yml:110`
**Symptom:** Healthcheck is `curl -f http://localhost:5678/healthz`, but the n8n image (we pinned to `latest` after the original `1.80` tag was missing) does not include `curl`. The container itself runs and serves the UI on port 5678; only the healthcheck reports failure.
**Fix:** Either install `curl` in a derived image, or use `wget --spider -q http://localhost:5678/healthz`, or call the healthcheck via a Node one-liner that's already present.

### B5 — `init-db.sh` enables `pgvector` against `postgres:17-alpine`
**File:** `project/scripts/init-db.sh:12`, `docker-compose.yml:5`
**Symptom:** `CREATE EXTENSION IF NOT EXISTS vector` fails because the alpine image doesn't bundle pgvector. The script swallows it with `|| true`, so the container starts cleanly. No model uses vector columns yet, so no functional impact.
**Fix:** Switch to `pgvector/pgvector:pg17` image when embeddings are actually needed, or drop the line.

---

## Functional gaps (features described in README/AGENTS that aren't wired)

### G1 — Poller is implemented but nothing schedules it
**Files:** `project/backend/app/services/ebay/poller.py`, `app/api/v1/endpoints/search.py`
**Symptom:** `EbayPoller.search_all()` and `search_item()` are written and would work end-to-end against the mock client, but `POST /search/trigger/{item_id}` and `POST /search/trigger-all` are stubs that return zeros without calling the poller. There is no APScheduler / Celery beat / FastAPI background task / n8n cron actually invoking the poller on an interval.
**Impact:** No listings ever get inserted → no deals get scored → no alerts. The dashboard sits at zero forever.
**Fix:** wire the trigger endpoints to actually call the poller, then add a periodic scheduler (the README implies n8n should host the cron — workflow JSONs aren't in the repo).

### G2 — Notification services exist but nothing dispatches them
**Files:** `project/backend/app/services/notifications/{telegram,email}.py` (not yet inspected for completeness)
**Symptom:** No code path calls these services after a deal is scored. There is no `NotificationDispatcher` and no `aiosmtplib` or telegram lib pinned in `pyproject.toml`.
**Fix:** add a dispatcher invoked from a "deal scored" hook (e.g. after `POST /deals/score/{listing_id}` or from a future poller-completion event), and add the missing dependencies.

### G3 — `make test` references a non-existent `tests/` directory
**File:** `project/Makefile:16`
**Symptom:** `pytest tests/ -xvs` fails with "No such file or directory".
**Fix:** Add a `backend/tests/` directory with at least a smoke test (`pytest tests/test_health.py`) so CI and the Makefile target both work.

### G4 — `register` endpoint creates a user without notification settings
**File:** `project/backend/app/api/v1/endpoints/auth.py`
**Symptom:** New users created via `/auth/register` won't have a row in `notification_settings`. The settings endpoint lazily creates one on GET, but PUT raises 404 if the row doesn't exist (`update_settings` doesn't auto-create).
**Fix:** Either auto-create on register, or have PUT upsert.

### G5 — `app/items/page.tsx` has no error UI for failed updates
Cosmetic — `toggleItem`/`deleteItem`/`updateInterval` all `await` the API but if it throws (e.g. the user's token expired), the optimistic UI update has already happened. Add a try/catch + revert + toast.

---

## Auth & security hardening

### S1 — Auth guard is client-side only
**File:** `project/frontend/components/auth-guard.tsx`
**Symptom:** The guard checks `localStorage.getItem("token")` in a `useEffect` and redirects. Server-rendered HTML for protected pages still ships before the redirect runs (visible flash of dashboard before bouncing to /login). Anyone can also fetch the static HTML directly.
**Fix:** Move auth to Next.js middleware (`middleware.ts`) reading a cookie-based session token, and have the login page write to an httpOnly cookie via a Next route handler that proxies to the backend.

### S2 — Token in `localStorage`, not httpOnly cookie
Same root cause as S1. `localStorage.getItem("token")` is XSS-readable. For a homelab demo this is fine; flag for production.

### S3 — `SECRET_KEY` defaults to `"change-me-in-production-min-32-chars"`
**Files:** `project/.env.example`, `docker-compose.yml:53`
Already a placeholder, but the default in `docker-compose.yml` lets the stack start with the placeholder if `.env` is missing the var. Consider failing loud (no default) for `SECRET_KEY` in production.

### S4 — CORS allows only `FRONTEND_URL`
**File:** `project/backend/app/main.py:14-20`
`allow_origins=[settings.FRONTEND_URL]` is fine for local. If you ever serve the frontend from multiple origins (e.g. lab subdomain + localhost), this needs to become a list.

### S5 — `/auth/register` is publicly open
**File:** `project/backend/app/api/v1/endpoints/auth.py:12`
Anyone reachable on the network can create accounts. For a single-user homelab tracker, gate this behind an env flag (`ALLOW_REGISTRATION=false`) or remove the endpoint entirely.

---

## Infra / build hygiene

### I1 — `docker-compose.yml` `version: "3.8"` is obsolete in Compose v2
**File:** `project/docker-compose.yml:1`
Just a warning every `docker compose` invocation prints. Remove the line.

### I2 — Backend Dockerfile installs `[dev]` extras into the production image
**File:** `project/backend/Dockerfile:7`
`uv pip install --system -e ".[dev]"` pulls pytest, ruff, pytest-asyncio, pytest-cov into the runtime image (~50MB+ bloat). Split into two stages (one with deps for tests, one prod-only).

### I3 — Backend uses `uv pip install` but doesn't lock dependencies
There is no `uv.lock` or `requirements.lock`. Reproducible rebuilds aren't guaranteed. Run `uv lock` and commit the lockfile.

### I4 — `BACKEND_HOST_PORT=8001` is needed because vLLM owns 8000
**File:** `project/docker-compose.yml:48`
We remapped the host port to avoid colliding with the user's vLLM process. `NEXT_PUBLIC_API_URL` and `.env.example` reflect this. If vLLM is moved or the stack runs on a different host, restore `8000:8000` and revert `NEXT_PUBLIC_API_URL`. The override env var (`BACKEND_HOST_PORT`) is in place so this is one edit.

### I5 — `n8n` pinned to `latest`
**File:** `project/docker-compose.yml:87`
We had to swap from `1.80` (manifest unknown) during the first run. `latest` is fine for now but pin to a real semantic version (e.g. `1.118.0` or whatever the current stable is) for reproducibility.

### I6 — No `Makefile` target rebuilds frontend after `NEXT_PUBLIC_API_URL` change
The frontend Next.js build bakes `NEXT_PUBLIC_*` env vars into the client bundle at build time. `make up` won't pick up `.env` changes that affect the frontend without `make build` first. Document this, or have `make up` always invoke `docker compose build`.

**Note 2026-05-15:** Hit this immediately during first browser login. The Dockerfile didn't pass `NEXT_PUBLIC_API_URL` as a build arg, so the bundle fell back to `"/api"`, the browser then hit `localhost:3000/api/...`, Next.js server-side rewrote it to `localhost:8001` — which inside the frontend container points to nothing (backend is at `backend:8000` on the docker network). Fixed by adding `ARG NEXT_PUBLIC_API_URL` + `ENV` to `frontend/Dockerfile` and `build.args.NEXT_PUBLIC_API_URL` in `docker-compose.yml`. Any future change to that env var still needs `docker compose build frontend` to take effect — `make up` doesn't rebuild.

### I7 — `Makefile` `seed` target uses `psql` interactively without checking for prior seeds
**File:** `project/Makefile:28`
Re-running `make seed` on a populated DB will fail on PK conflicts (the user table has `ON CONFLICT (username) DO NOTHING`, but `tracked_items` does not). Add `ON CONFLICT (name) DO NOTHING` or wrap in a transaction.

### I8 — Frontend `Dockerfile` doesn't copy `node_modules` for runtime when not using Next standalone correctly
Worked on the first build. If anyone touches the Dockerfile, note that `output: 'standalone'` in `next.config.ts` is what makes the runtime image self-contained; removing it will break the COPY.

### I9 — `passlib[bcrypt]` requires `bcrypt<4.0`
**File:** `project/backend/pyproject.toml`
We added the pin during this pass. The long-term fix is to migrate off `passlib` (which is unmaintained) to direct `bcrypt`/`argon2-cffi` use. Track this so the pin doesn't silently rot.

### I10 — `alembic.ini` was originally inside `alembic/`
**File:** moved during this pass to `project/backend/alembic.ini`
The default alembic CLI looks for `./alembic.ini` in CWD. Keep it at the backend root and `script_location = alembic` resolves correctly. Don't move it back without also updating the Dockerfile CMD to use `alembic -c alembic/alembic.ini upgrade head`.

---

## Catalog / data quality

### D1 — Catalog and seed both hard-code the same 34 items independently
**Files:** `project/backend/app/services/ebay/catalog.py` and `project/backend/scripts/seed_data_v2.sql`
The 34-item list is duplicated in two places (Python class + SQL inserts). Drift between them will confuse Add Item suggestions vs. what's tracked. Consider generating the SQL from the Python catalog.

### D2 — Some catalog `BENCHMARK_PRICES` keys disagree with the catalog medians
**File:** `project/backend/app/services/scoring/engine.py:8-18`
`BENCHMARK_PRICES["epyc 7f72"]=350` but `HardwareCatalog`'s EPYC 7F72 has `benchmark_median=375`. Two sources of truth → scoring will use whichever fires first in the keyword match. Drop `BENCHMARK_PRICES` and always read from the catalog.

### D3 — Catalog HDD entries use `category_id="56083"`
The HDD entries (Exos, Ultrastar, MG08/09) share the same category as enterprise SSDs. eBay distinguishes HDDs from SSDs at the category level. Searches will be polluted with the wrong device class. Verify the eBay category IDs and split if needed.

---

## Tests

### T1 — Zero test coverage
There are no unit tests, no integration tests, no smoke tests. Phase 9 of the plan calls them out but nothing has been written. Minimum useful first additions:
- `tests/test_health.py` — hits `/api/v1/health`
- `tests/test_auth.py` — register + login round trip
- `tests/test_scoring.py` — feed `DealScoringEngine` known inputs, assert outputs
- `tests/test_rate_budget.py` — verify `RateBudgetManager` enforces the buffer + near-limit logic
- `tests/test_catalog.py` — verify catalog has 34 items and every item has non-zero `scam_floor` (where claimed) and matching benchmark prices

### T2 — No CI workflow
No `.github/workflows/`. Once tests exist, run them on every PR.

---

## Documentation

### DOC1 — `README.md` says backend is on `http://localhost:8000`
**File:** `README.md:78-80`
After the host-port remap to 8001, the docs are stale. Update or document the override.

### DOC2 — `AGENTS.md` and `.agents/*.md` describe modules in `backend/app/...` while the actual code lives in `project/backend/app/...`
The recent "update path" commit moved code into `project/`, but the AGENTS index docs weren't updated. Either update each `.agents/*.md` to use `project/backend/...` paths, or move the code back up to the repo root.

### DOC3 — README claims "n8n workflow engine" but no workflow JSONs exist
**File:** `README.md:80`
`workflows/` directory mentioned in `plan/PHASE_07.md` is missing. Either create stub workflows or remove the n8n service from the stack (it's currently doing nothing useful).

---

## Summary of "actually broken vs. nice-to-have"

| Severity | Count | Examples |
|----------|-------|----------|
| Bugs (will misbehave) | 5 | B1 (eBay filters), B2 (model defaults), B3 (priority_tier), B4 (n8n health), B5 (pgvector) |
| Functional gaps | 5 | No scheduler, no dispatcher, no tests dir, no settings auto-create on register, no error UI |
| Security | 5 | Client-side guard, localStorage token, default SECRET_KEY, CORS, open registration |
| Infra hygiene | 10 | Compose version, dev deps in prod, no lockfile, port remap, n8n pin, etc. |
| Data quality | 3 | Catalog/seed duplication, benchmark drift, HDD/SSD category collision |
| Tests | 2 | Zero coverage, no CI |
| Docs | 3 | Port mismatch, path mismatch, missing workflows |

**Recommended next session:** start with G1 (wire poller to a scheduler) and B1 (fix the eBay filter bug) so a real `USE_MOCK_EBAY=false` run can produce listings. Then T1 (smoke tests) to lock in current behavior before further changes.
