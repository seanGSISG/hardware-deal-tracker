# Mega Plan Findings

Project: Hardware Deal Tracker — MVP2
Created: 2026-06-02

Shared findings across all features. Feature-specific findings live in their worktrees.

---

## Current-state map (verified 2026-06-02 via codebase fan-out)

**Already done (do NOT redo):**
- `client.py` — OAuth scope is the global `api_scope`; filter f-string `{{ }}` bug is FIXED. eBay creds wired, `USE_MOCK_EBAY=false`, real Browse search verified (155 results).
- `EbayPoller` — fully implemented: `__init__(redis_client=None)`, `search_item(db, item)`, `search_all(db)`; uses `RateBudgetManager`, `DeduplicationEngine`, `ListingParser`.
- `email.py` — `send_email` AND `send_deal_alert` both implemented (uses BLOCKING `smtplib` — migrate to aiosmtplib).
- `telegram.py` — `send_deal_alert` fully implemented.
- `NotificationSetting` — correct fields: `telegram_min_score=70`, `email_min_score=50`, `email_enabled`, `telegram_enabled`, `email_address`, `email_digest_mode="daily"`, `mute_until`. No `alert_threshold`.
- `HardwareCatalog` — 34 items, each with `benchmark_median`.
- `RateBudgetManager` — `can_search(priority)`; 5000 limit / 200 buffer / 4000 near-limit.
- `docker-compose.yml` — no `version:` line (I1 already a no-op).

**Open gaps:**
- `search.py` endpoints — STILL hardcoded stubs (trigger/{id}, trigger-all).
- `main.py` — NO lifespan, NO scheduler.
- `config.py` — uses deprecated `class Config`; MISSING `SCHEDULER_ENABLED`, `POLL_SCHEDULER_INTERVAL`, `ALLOW_REGISTRATION`, `NOTIFICATIONS_ENABLED`, `SMTP_FROM`.
- `pyproject.toml` — no `apscheduler`; no `real_ebay` marker.
- **Poller never calls the scoring engine** (gap beyond the written plan — see ADR-006).
- `dispatcher.py` — MISSING; notifications are dead code (zero call sites).
- `/auth/register` — fully public (no `ALLOW_REGISTRATION`).
- `PUT /settings/notifications` — 404s on missing row (GET lazy-creates).
- SECRET_KEY — no fail-loud check; placeholder default.
- Frontend — no toast library; `app/items/page.tsx` optimistic handlers lack try/catch.
- `BENCHMARK_PRICES` — 22-entry dict in `engine.py`, drifts from catalog.
- `seed_data_v2.sql` — tracked_items inserts NOT idempotent; no `generate_seed.py`.
- 7 model columns have Python `default=` but no `server_default=`; `priority_tier` is a `@property` (not `@computed_field`).
- `items.py` `list_items` — no `response_model` (priority_tier added via manual dict helper).
- `backend/Dockerfile` — multistage BUT runtime copies dev deps from builder (pytest/ruff in prod image).
- `Makefile up` — no `docker compose build` first.
- `.github/workflows/` — MISSING (no CI).
- `backend/tests/` — MISSING (no conftest, no tests).
- n8n — still in compose (service + `n8n_data` volume).

---

## Project-Wide Decisions

See `design_doc.json` / `design_doc.md` ADR-001 … ADR-009. Highlights:
- ADR-002: serial-phase rule REMOVED from `plan/MVP2.md`; dependency-driven parallel worktrees.
- ADR-006: scoring wired into the poll path (keystone gap).
- ADR-005: app MUST run from an empty catalog; seed = optional starter data.

## Shared Patterns

- **SourceAdapter** interface (feature-001 introduces, feature-005 extends) — normalized listing shape: `title, price, shipping, total, condition, url, source, seller, raw_payload`.
- FastAPI `Depends(get_db)` + `Depends(get_current_user)` everywhere.

## Integration Notes (shared-file coordination — merge-conflict hotspots)

Batch-2 features run in parallel worktrees off data-flow-merged `main`. Watch these shared files at merge time:
- **`app/core/config.py`** — feature-001 OWNS the SettingsConfigDict migration + scheduler vars; feature-003 adds `ALLOW_REGISTRATION`/`NOTIFICATIONS_ENABLED`/`SMTP_FROM`; feature-006 adds AI vars. Land feature-001 first (it's the keystone), others rebase.
- **`app/services/scoring/engine.py`** — feature-001 (scoring-in-poll) and feature-004 (drop BENCHMARK_PRICES) both edit. Coordinate.
- **`app/services/ebay/poller.py` / client** — feature-001 wires scheduler+scoring; feature-005 refactors into SourceAdapter. feature-005 depends on feature-001 merged.
- **`seed_data_v2.sql`** — feature-002 (idempotent ON CONFLICT) and feature-004 (generate_seed.py) both touch. feature-004 owns generation; feature-002 adds idempotency to the generated output.
- **scheduler job registration in `main.py` lifespan** — feature-001 (poll tick), feature-003 (digest job), feature-006 (price-history snapshot). Use distinct job ids.

## Source research

**Source #2 = PCPartPicker (Sean's directive, 2026-06-02; research COMPLETE → `plan/MVP2_PCPARTPICKER_RESEARCH.md`):** **BENCHMARK/REFERENCE source ONLY** — refresh `benchmark_median` + add a 'vs retail' delta; **do NOT** route through the eBay scoring/dedup/notification pipeline (condition always `new`). Reuse `lucwl/pypartpicker`'s data model (`Part`/`Vendor`/`Price`/specs + `response_retriever` hook), **replace** its stale requests-html/pyppeteer transport (Cloudflare flags it). `docyx/pc-part-dataset` = one-time spec bootstrap; `N-O-U-R` = paid-ZenRows, skip. Overlap only ~10-12 of 34 items (workstation GPU, consumer NVMe/SSD, non-ECC DDR, Threadripper) via optional `pcpp_product_id`; **useless** for EPYC / ECC-RDIMM / enterprise HDD / server boards. No public JSON API (staff refuse); **ToS forbids scraping** → keep minimal/cached/disableable. Anti-bot cheapest-first ($0/mo, ~10-12 pages/day): `curl_cffi` TLS-impersonation + caching → **RESIDENTIAL** Tailscale exit (**NOT** datacenter `104.223.27.177` — Cloudflare flags datacenter ranges) → Nodriver/FlareSolverr for clearance cookies → paid API (Zyte/Bright Data) behind a flag, last resort. Own ≤200/day bucket, `ENABLE_PCPARTPICKER=false` default, circuit-breaker on Cloudflare errors. Feeds feature-004 (benchmark_median) + feature-006 ('vs retail' delta).

**Source #3+ = Shopify used-server retailers** (`plan/MVP2_SOURCE_RESEARCH.md`, 2026-06-02): most run **Shopify** with public `/products.json` + schema.org JSON-LD → generic **ShopifyJsonLdAdapter**. Onboard **TechMikeNY → UnixSurplus → ServerMonkey**. **Defer** Amazon PA-API (sales quota + no price caching) and Micro Center (anti-bot, consumer parts) to MVP3. Dedup on `(source, source_listing_id)` — TechMikeNY appears in both its site and the eBay feed. Per-source rate buckets (separate from eBay's 5000/day). Verify platform + robots.txt/ToS per site before coding each adapter.
