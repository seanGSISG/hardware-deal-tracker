# MVP3 Deferred Backlog — consolidated "things we put off"

> Date: 2026-06-02 · Base: main@6adf055 (MVP2 merged)
> Canonical inventory of every item deferred across MVP1→MVP2, cross-referenced to the MVP3
> mega-plan. Each item has a **disposition**: which MVP3 feature absorbs it, or MVP4 / won't-do.
> Sources cited inline. Code is clean (no lingering TODO/FIXME); deferrals live in the docs.

---

## A. Data sources we keep putting off

The MVP2 source research (`plan/MVP2_SOURCE_RESEARCH.md`) ranked sources; MVP2 shipped eBay + built
(dormant) Shopify adapters for TechMikeNY/UnixSurplus/ServerMonkey. The rest were deferred:

| Source | Type | Why deferred | Disposition |
|--------|------|--------------|-------------|
| **TechMikeNY / UnixSurplus / ServerMonkey** | Shopify `/products.json` + JSON-LD | adapters built in MVP2, never enabled | **MVP3 feature-003** (go-live) |
| **Cloud Ninjas** | Shopify-class, "easy" | not yet onboarded | **MVP3 feature-003** (next easy Shopify adapter) |
| **SaveMyServer** | weekly-refreshed pricing | good **memory price signal** during DDR4 shortage; refresh cadence is slow | **MVP3 feature-003** (benchmark-signal, low cadence) |
| **Natex** | Shopify-class | high deal-density on cheap DDR4 / NICs / barebones | **MVP3 feature-003** (candidate after the 3 primaries) |
| **Reddit r/homelabsales** | peer-to-peer marketplace (OAuth API, free tier) | **free-text, unstructured** → heavy NLP; items sell fast; high signal-to-noise cost | **MVP3 feature-007 (stretch)** or MVP4 — "community-signal" pipeline, NOT a price-poll adapter |
| **ServeTheHome (STH) forums** | XenForo deals threads | scrape + free-text NLP | **MVP3 feature-007 (stretch)** / MVP4 — same community-signal pipeline |
| **Amazon Renewed (PA-API 5.0)** | sanctioned API, clean fields | Associates gate (**10 qualified sales / 30 days**), ~1 req/s, **no static price caching** | **MVP4** — feature-003 records a go/no-go; do not block on Associates |
| **Micro Center** | retailer | anti-bot, consumer-focused, in-store pricing | **MVP4** — feature-003 records go/no-go |
| **PCPartPicker** | benchmark/reference only | ToS forbids scraping, no public API, Cloudflare | MVP2 built it gated OFF; **MVP3 feature-003** makes it runnable behind residential egress + populates `pcpp_product_id` |

**Cautionary note (carried):** `FocusedLoop/PC-Part-Picker-Scrapper-Bot` was abandoned because Cloudflare
blocked its VPN-IP rotation — datacenter/VPN IP rotation alone is dead; PCPartPicker needs **residential**
egress (Tailscale exit on Sean's homelab, NOT `104.223.27.177`).

### Community-signal pipeline (Reddit + STH) — design note
Distinct from price-poll adapters: posts are unstructured prose. Needs an NLP extraction stage
(price/condition/model from free text), aggressive dedup, and a "sold/traded" detector. Treat as a
separate ingestion class feeding *leads/alerts*, not the scored-listing pipeline. The configured AI
provider (OpenRouter/vLLM) can do the extraction — ties into feature-006/AIClient.

---

## B. eBay API constraints (future)

- **Higher daily caps require eBay's Application Growth Check** (`plan/MVP2_PREFLIGHT.md:134`) — out of
  scope until poll volume actually approaches 5,000/day across many tracked items. **MVP4 / when needed.**
  feature-004 should document the current 5,000/day ceiling + the growth-check path in the README.
- **eBay sold/completed comps may not be exposed to the Browse app token** — feature-001's fallback is to
  accumulate our own `PriceHistory` as the rolling baseline; document the limitation. **MVP3 feature-001.**

---

## C. Security / auth backlog (DEFERRED_ISSUES.md S-series)

| Item | Status | Disposition |
|------|--------|-------------|
| S1 — client-side-only auth guard (flash-of-dashboard) | OPEN | **MVP3 feature-002** (Next middleware) |
| S2 — token in localStorage (XSS-readable) | OPEN | **MVP3 feature-002** (httpOnly cookie) |
| S3 — SECRET_KEY default | CLOSED in MVP2 (fail-loud boot guard) | done |
| S4 — CORS single-origin | OPEN | **MVP3 feature-002** (multi-origin allowlist) |
| S5 — open registration | CLOSED in MVP2 (`ALLOW_REGISTRATION`) | done |

---

## D. Quality / infra hygiene (DEFERRED_ISSUES.md I-series + this session)

| Item | Disposition |
|------|-------------|
| ~143 legacy ruff violations; CI ruff is `continue-on-error` | **MVP3 feature-004** — clear + flip to blocking |
| I9 — migrate `passlib` → `bcrypt`/`argon2-cffi` (passlib unmaintained, `bcrypt<4` pin) | **MVP3 feature-004** |
| Frontend never build-verified (MVP2) — sonner per-handler toasts unwired, PriceTrendChart unverified | **MVP3 feature-005** (mandatory `next build`) |
| I4 — backend host port 8001 (vLLM owns 8000) | doc only — feature-004 README refresh |
| I5/B4 — n8n pin/health | RESOLVED (n8n removed in MVP2); feature-004 strikes the doc refs |
| pgvector (B5) on `postgres:17-alpine` | **MVP3 feature-006 (stretch)** — switch image only if semantic matching ships |

---

## E. Data quality / catalog (DEFERRED_ISSUES.md D-series)

| Item | Disposition |
|------|-------------|
| D1 — catalog/seed duplicated in two places | CLOSED in MVP2 (`generate_seed.py`) |
| D2 — `BENCHMARK_PRICES` drifts from catalog | CLOSED in MVP2 (dropped the dict) |
| D3 — HDD entries share SSD category id `56083` → polluted searches | OPEN → **MVP3 feature-004** (split HDD/SSD category ids) |
| `pcpp_product_id` mappings unpopulated (the ~10-12 mappable items) | **MVP3 feature-003** (populate for workstation GPU / consumer NVMe / non-ECC DDR / Threadripper) |
| Price-trend signal ("DDR4 RISING — buy sooner", per research) not surfaced | **MVP3 feature-001** emits trend direction; feature-005 surfaces it |

---

## F. Docs (DEFERRED_ISSUES.md DOC-series)

| Item | Disposition |
|------|-------------|
| DOC1 — README backend port stale (8000→8001) | **MVP3 feature-004** |
| DOC2 — AGENTS.md / `.agents/*.md` paths predate the `project/` move | **MVP3 feature-004** |
| DOC3 — README claims n8n workflow engine (now removed) | **MVP3 feature-004** |
| `DEFERRED_ISSUES.md` final reconciliation never done (MVP2.md exit criterion: strike closed items + add a "Punted from MVP2" section) | **MVP3 feature-004** — reconcile against this backlog |

---

## G. Integrations / misc deferred

| Item | Why put off | Disposition |
|------|-------------|-------------|
| **paperless** (receipt/invoice archiving of purchases) | "keep as MVP3 if at all" (`plan/MVP2.md:23`); Sean's stated pref = optional | **MVP4 / optional** — record a decision in feature-004; out of core MVP3 scope |
| Bitwarden temp session cleanup (`/tmp/.bwsess`, `/tmp/.bwerr`) | leftover from eBay-creds session | **VERIFIED CLEAN 2026-06-02** (no action) |
| P2 "Monitor / future buys" tier polishing (`plan/PLAN.md`) | original tiered-polling concept | covered by existing P0–P3 selector; no action |

---

## Disposition summary

- **Folded into MVP3 mega-plan:** feature-001 (sold-comps + trend signal), feature-002 (S1/S2/S4),
  feature-003 (Shopify go-live + Cloud Ninjas/SaveMyServer/Natex + PCPartPicker egress + `pcpp_product_id`
  + Amazon/MicroCenter go/no-go + eBay growth-check note), feature-004 (ruff/bcrypt/D3/docs +
  DEFERRED_ISSUES reconciliation + paperless decision), feature-005 (frontend surfacing + build verify),
  feature-006 (pgvector stretch), **feature-007 NEW** (community-signal Reddit/STH NLP, stretch).
- **Explicitly MVP4 / when-needed:** Amazon PA-API, Micro Center, eBay Application Growth Check, paperless,
  full community-signal productionization.
- **Already closed in MVP2 (struck):** S3, S5, D1, D2, I1, I5/B4, B1, B2, B3, G1–G5, T1, T2.
