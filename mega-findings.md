# Mega Plan Findings — MVP3

Project: Hardware Deal Tracker — MVP3 (harden + surface)
Created: 2026-06-02
Base: main@6adf055 (MVP2 fully merged; 165 backend tests pass, single alembic head `ai_analyses`)

Shared findings across MVP3 features. Feature-specific findings live in their worktrees.

---

## Current-state map (post-MVP2, verified this session)

**Backend already in place (build on it, don't redo):**
- Poll loop: `EbayPoller.search_item/search_all` → SourceAdapter (`app/services/sources/`), dedup on `(source, source_listing_id)`, scoring (`DealScoringEngine`), `ListingScore` + `PriceHistory` persisted per new listing, best-effort `NotificationDispatcher` + `AIAnalyzer` (both gated). APScheduler `poll_tick` + `digest_tick` jobs in `app/main.py` lifespan.
- `EbayPoller._historical_stats_for(item)` returns `{}` (the seam feature-001 fills). The engine already consumes `median_price/avg_price/std_dev/min_price/data_points` and falls back to `catalog_item.benchmark_median`.
- SourceAdapters: `EbayBrowseAdapter` (live), `PcPartPickerAdapter` (benchmark-only, `ENABLE_PCPARTPICKER=false`), `ShopifyJsonLdAdapter` (built, dormant). Per-source rate buckets via `SourceRateBudget`.
- AI: `app/services/ai/{client,analysis}.py` — configurable OpenRouter/vLLM, `AIAnalysis` model + `/api/v1/ai/{listing_id}` endpoint. Opt-in `AI_ENABLED`.
- Price history: `PriceHistory` model + `/api/v1/price-history/{item_id}` time-series endpoint.
- Auth: JWT bearer; `/auth/register` gated by `ALLOW_REGISTRATION`; SECRET_KEY fail-loud; `get_current_user` (`app/api/deps.py`). **Still client-side localStorage on the frontend** (feature-002 fixes).
- Tests: `tests/conftest.py` has `db` (in-memory async sqlite), `client` (stub-auth), `unauth_client`, `admin_client` fixtures. `real_ebay` marker registered + creds-gated.
- CI `.github/workflows/ci.yml` runs pytest (pg+redis services); **ruff step is `continue-on-error: true`** (feature-004 flips it). ~143 legacy ruff violations remain in untouched files.

**Frontend already in place:**
- Next.js 15 App Router, dark monospace/amber design system (see screenshots). `lib/api.ts` is the single API client. `sonner` Toaster mounted in `app/layout.tsx` (per-handler wrapping NOT done — feature-005). `PriceTrendChart` (recharts) wired into the item-detail HISTORY tab but **never build-verified** (no node_modules in worktrees). Item detail has tabs TRACKING / LIVE LISTINGS(n) / HISTORY / NOTES; LIVE LISTINGS still a placeholder count.

## Project-Wide Decisions

See `design_doc.json` / `design_doc.md` ADR-001..ADR-006. Highlights: ADR-001 sold-comps baseline; ADR-002 cookie+middleware auth; ADR-003 Shopify scored / PCPartPicker benchmark-only; ADR-004 strict CI lint + bcrypt; ADR-005 design system authoritative + build-verified; ADR-006 pgvector optional.

## Shared Patterns
- Graceful degradation everywhere (sold-comps, AI, semantic all fall back; app runs from empty DB).
- SourceAdapter + per-source rate buckets; dedup `(source, source_listing_id)`.
- Frontend reuses `lib/api.ts` + existing monospace/amber components; **every frontend change runs `npm install && next build`**.

## Integration Notes (shared-file merge hotspots for parallel worktrees)
- `app/services/ebay/poller.py` — feature-001 edits `_historical_stats_for`; keep the existing scoring/dispatch/AI/price-history wiring intact.
- `app/core/config.py` — feature-002 (CORS list), feature-003 (source flags exist), feature-006 (pgvector/embedding vars) add vars; append, don't rewrite.
- Frontend `lib/api.ts`, `components/*`, `app/items/[id]/page.tsx` — feature-002 OWNS auth files (auth-guard/middleware/login/api-auth); feature-005 owns the surfacing components. feature-005 depends on 001+002+003 so it branches off their merged result (avoids frontend/auth conflicts).
- `pyproject.toml` — feature-004 owns the ruff config flip + bcrypt dep swap.
- Migrations — feature-001 (rolling-stats snapshot), feature-006 (vector column) each add a migration; chain linearly after the current head `ai_analyses` (re-thread `down_revision` at merge time so there's one head).

## Source research (carried from MVP2)
- Shopify retailers (TechMikeNY/UnixSurplus/ServerMonkey): public `/products.json` + JSON-LD; verify robots.txt/ToS per site before enabling.
- PCPartPicker: ToS forbids scraping, no public API → benchmark-only, residential egress (NOT datacenter `104.223.27.177`), cache, disableable.
- Amazon PA-API + Micro Center: deferred (Associates quota / anti-bot); feature-003 records a go/no-go for MVP4.
- bullseye-app sold-comps pattern (AGPL — reimplement from idea, don't copy): Tukey-trimmed 90d median + IQR over eBay sold comps → feature-001.
