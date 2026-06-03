# Deferred Issues — Hardware Deal Tracker

After the first-build pass on 2026-05-15, the stack starts cleanly: `docker compose up -d` brings all services up, `alembic upgrade head` applies the schema, the seed inserts 34 items + admin, login + JWT works, all 13 API endpoints return 200 on the smoke test, and all 8 frontend routes render. The fixes that got us there are described in `/home/adminuser/.claude/plans/please-review-this-codebase-sunny-torvalds.md`.

This file lists everything that was **intentionally not fixed** during that pass — bugs that don't block the demo but should be addressed before this is treated as production. Items are grouped by severity and scope.

---

## Reconciliation status (updated 2026-06-02 — feature-004)

> Reconciled against `plan/MVP3_DEFERRED_BACKLOG.md` (the MVP2 exit-criterion that was
> never done). Each original item below is annotated inline with **[CLOSED-in-MVP2]**,
> **[feature-00X]** (folded into an MVP3 feature), or **[MVP4]**. The per-item disposition
> table is the single source of truth; the original prose is retained for history.

| Item | Disposition |
|------|-------------|
| **B1** eBay filter f-strings | **CLOSED-in-MVP2** (real Browse client fixed; `real_ebay` smoke test covers it) |
| **B2** model defaults vs raw-SQL seed | **CLOSED-in-MVP2** (`server_default` added + migration; `test_server_defaults.py`) |
| **B3** `/items` omits `priority_tier` | **CLOSED-in-MVP2** (`response_model` wrapper added) |
| **B4** n8n container unhealthy | **CLOSED-in-MVP2** (n8n removed from the stack; `test_no_n8n.py`) |
| **B5** pgvector on alpine | OPEN → **feature-006** (stretch; switch image only if semantic matching ships) |
| **G1** poller not scheduled | **CLOSED-in-MVP2** (APScheduler `poll_tick`/`digest_tick` in `app/main.py`) |
| **G2** notifications not dispatched | **CLOSED-in-MVP2** (`NotificationDispatcher` + aiosmtplib/telegram wired) |
| **G3** `make test` no tests dir | **CLOSED-in-MVP2** (`tests/` added; ~165→184 tests green) |
| **G4** register without notification settings | **CLOSED-in-MVP2** (settings auto-create/upsert) |
| **G5** no error UI on failed item updates | **CLOSED-in-MVP2** (toast + revert); UI polish continues in **feature-005** |
| **S1** client-side-only auth guard | OPEN → **feature-002** (Next middleware) |
| **S2** token in localStorage | OPEN → **feature-002** (httpOnly cookie) |
| **S3** SECRET_KEY default | **CLOSED-in-MVP2** (fail-loud boot guard; `test_security_boot.py`) |
| **S4** CORS single-origin | OPEN → **feature-002** (multi-origin allowlist) |
| **S5** open registration | **CLOSED-in-MVP2** (`ALLOW_REGISTRATION` gate) |
| **I1** compose `version: "3.8"` obsolete | **CLOSED-in-MVP2** (removed) |
| **I5 / B4** n8n pin/health | **CLOSED-in-MVP2** (n8n removed); feature-004 struck the doc refs |
| **I9** migrate passlib → bcrypt (`bcrypt<4` pin) | **CLOSED → feature-004** (direct bcrypt + verify/rehash-on-login; pin dropped) |
| **D1** catalog/seed duplicated | **CLOSED-in-MVP2** (`generate_seed.py` single source of truth) |
| **D2** `BENCHMARK_PRICES` drift | **CLOSED-in-MVP2** (dict dropped; catalog is authoritative) |
| **D3** HDD/SSD share category `56083` | **CLOSED → feature-004** (HDD 56083 / SSD 175669 split + seed regen) |
| **T1** zero test coverage | **CLOSED-in-MVP2** (full pytest suite) |
| **T2** no CI workflow | **CLOSED-in-MVP2** (`.github/workflows/ci.yml`; feature-004 makes ruff blocking) |
| **DOC1** README port stale | **CLOSED → feature-004** (8001 host / 8000 internal documented) |
| **DOC2** `.agents/*` paths predate `project/` move | **CLOSED → feature-004** (paths updated) |
| **DOC3** README claims n8n engine | **CLOSED → feature-004** (n8n refs removed) |
| **DEFERRED_ISSUES reconciliation** (this) | **CLOSED → feature-004** |
| Sold-comps / price-trend signal | **feature-001** |
| Shopify go-live / PCPartPicker egress / `pcpp_product_id` | **feature-003** |
| Frontend surfacing + build verify | **feature-005** |
| Community-signal (Reddit/STH NLP) | **feature-007** (stretch) → may slip to MVP4 |
| **I2/I3/I6/I7/I8/I10** build-hygiene minutiae | tracked; not in MVP3 critical path (I3 lockfile now present — `uv.lock` committed) |

See the **Punted to MVP4** section near the end of this file for the explicitly out-of-scope items.

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

### B4 — `n8n` container is unhealthy (cosmetic) — ✅ CLOSED-in-MVP2 (n8n removed; doc refs struck in feature-004)
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

### I9 — `passlib[bcrypt]` requires `bcrypt<4.0` — ✅ CLOSED (feature-004)
**File:** `project/backend/pyproject.toml`
We added the pin during this pass. The long-term fix is to migrate off `passlib` (which is unmaintained) to direct `bcrypt`/`argon2-cffi` use. Track this so the pin doesn't silently rot.
**Resolved (feature-004):** migrated `app/core/security.py` to direct `bcrypt` (verify existing `$2b$` hashes + `needs_rehash` rehash-on-login + deliberate 72-byte truncation). Dropped `passlib[bcrypt]` and the `bcrypt<4.0.0` pin; now `bcrypt>=4.0`. Covered by `test_password_hashing.py`.

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

### D3 — Catalog HDD entries use `category_id="56083"` — ✅ CLOSED (feature-004)
The HDD entries (Exos, Ultrastar, MG08/09) share the same category as enterprise SSDs. eBay distinguishes HDDs from SSDs at the category level. Searches will be polluted with the wrong device class. Verify the eBay category IDs and split if needed.
**Resolved (feature-004):** HDDs keep eBay US Internal-HDD `56083`; the U.2 NVMe enterprise SSDs (P5510, PM9A3, 7450) moved to the verified Internal-SSD leaf `175669` (confirmed live at `ebay.com/b/.../175669`). Seed regenerated via `generate_seed.py`; `test_storage_categories.py` asserts class-correctness.

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

### DOC1 — `README.md` says backend is on `http://localhost:8000` — ✅ CLOSED (feature-004)
**File:** `README.md:78-80`
After the host-port remap to 8001, the docs are stale. Update or document the override.
**Resolved (feature-004):** README + `.agents/DEPLOYMENT.md`/`DEVELOPMENT.md` now document host port **8001** (override `BACKEND_HOST_PORT`) → container **8000**.

### DOC2 — `AGENTS.md` and `.agents/*.md` describe modules in `backend/app/...` while the actual code lives in `project/backend/app/...` — ✅ CLOSED (feature-004)
The recent "update path" commit moved code into `project/`, but the AGENTS index docs weren't updated. Either update each `.agents/*.md` to use `project/backend/...` paths, or move the code back up to the repo root.
**Resolved (feature-004):** all bare `backend/...` and `frontend/...` references in `AGENTS.md`, `README.md`, and every `.agents/*.md` now use the `project/backend/...` / `project/frontend/...` paths that exist on disk.

### DOC3 — README claims "n8n workflow engine" but no workflow JSONs exist — ✅ CLOSED (feature-004)
**File:** `README.md:80`
`workflows/` directory mentioned in `plan/PHASE_07.md` is missing. Either create stub workflows or remove the n8n service from the stack (it's currently doing nothing useful).
**Resolved (feature-004):** n8n was removed from the stack in MVP2; feature-004 struck the remaining 14 n8n references across `AGENTS.md` and `.agents/*.md`. `grep -rin n8n` over the docs returns nothing.

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

> **Status note (2026-06-02):** the "Recommended next session" above is historical — G1, B1, and T1 were all completed in MVP2. See the Reconciliation status table at the top of this file.

---

## Punted to MVP4 (explicitly out of current scope)

These were evaluated and deliberately deferred past MVP3. None block MVP3; each is "when-needed / optional."

| Item | Why deferred | Re-entry condition |
|------|--------------|--------------------|
| **Amazon Renewed (PA-API 5.0)** | Associates gate (**10 qualified sales / 30 days**), ~1 req/s, no static price caching | MVP4 — feature-003 records a go/no-go; do not block on Associates |
| **Micro Center** | anti-bot, consumer-focused, in-store-only pricing | MVP4 — feature-003 records a go/no-go |
| **eBay Application Growth Check** | only needed once poll volume approaches the **5,000 calls/day** ceiling across many tracked items | MVP4 / when poll volume nears the cap (README documents the 5,000/day ceiling + growth-check path) |
| **paperless** (receipt/invoice archiving of purchases) | "keep as MVP3 if at all" (`plan/MVP2.md:23`); owner preference = **optional** | **MVP4 / optional** — see decision below; out of core MVP3 scope |
| **Full community-signal pipeline** (Reddit r/homelabsales + STH NLP, productionized) | unstructured free-text → heavy NLP, fast-moving, high signal-to-noise cost; a leads pipeline distinct from scored listings (ADR-007) | MVP3 feature-007 is a **stretch** prototype; full productionization is MVP4 |

### paperless decision (recorded — feature-004)
**Decision:** paperless (archiving purchase receipts/invoices) is **optional and out of scope for MVP3**, slated for **MVP4** at most. It is not a tracking/scoring capability and was explicitly flagged as "optional" by the owner (`plan/MVP2.md:23`). No code, dependency, or service is added for it in MVP3.

---

## Secrets hygiene (verified 2026-06-02 — feature-004)

- **Bitwarden temp session files** `/tmp/.bwsess` and `/tmp/.bwerr` are **absent** (verified `ls` returns not-found). No live Bitwarden session lingers.
- **No secrets committed in feature-004:** `git diff main...HEAD` for this feature contains no API keys, tokens, or private keys. Credential references in code are env-driven (`settings.*` / `os.getenv`), and the only credential-shaped strings in docs are placeholders (e.g. `<app-password>`, `<bot-token>`, `change-me-in-production-min-32-chars`). The live-smoke tests read creds exclusively from the environment and skip without them.
