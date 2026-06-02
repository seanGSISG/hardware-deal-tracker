# Build-vs-Adopt Research — Hardware Deal Tracker

> Date: 2026-06-02
> Method: 4-subagent research fan-out (deep-analyze ours · analyze pricebuddy · GitHub/web sweep ×2)
>   + a follow-up code-level fork assessment of clucraft/PriceGhost (license set aside, per Sean)
> Question: Should we keep building this project, or adopt/fork a recent public repo to save time?
> **Decision: CONTINUE BUILDING OURS.** No credible base to adopt. Mine a few repos for patterns only.

> NOTE on licensing: the unlicensed repos (Discount-Bandit, PriceGhost) are flagged below for
> awareness, but per Sean, license is HIS risk to manage and is NOT the deciding factor. The
> PriceGhost deep-dive below judges it on **technical/architectural merit alone** and still says
> don't fork — for stack + missing-hard-parts reasons, not licensing.

---

## TL;DR

The verdict was unanimous across four independent agents. Every traction-having open-source
tracker is either **legally unforkable (no license)**, **wrong stack (PHP/TS not Python/FastAPI)**,
or built on the **wrong paradigm** (scrape-a-known-URL-daily vs our API-search-against-a-curated-
catalog-with-rate-budgeting). **None** implement deal scoring or scam detection — our core
differentiator. The Python-stack matches are EOL-2019 or 0–4★ hobby projects. The closest full
product (hardwarehunter.io) is closed-source SaaS, which validates the market and confirms the OSS
lane is empty. Our bespoke IP — the 34-item enterprise-hardware catalog (~200–300 hrs to recreate),
6-component scoring, 4-layer eBay rate budget — is exactly what an off-the-shelf tracker would NOT
give us.

---

## Why not adopt (three structural reasons the whole field fails)

1. **Licensing.** The two feature-rich self-hosted options (Discount-Bandit, PriceGhost) ship with
   **no LICENSE file = all rights reserved** → cannot legally fork, modify, or redistribute.
2. **Wrong paradigm.** They scrape a user-pinned **product-page URL on a daily cron** with a single
   user-set price/percent threshold. We do **API-based marketplace search** across a query, against a
   **curated catalog**, with **rate budgeting** and **tiered polling**. The data models (Store→Product→
   URL→Price) don't map onto (Catalog item → eBay query → scored listings).
3. **Stack + missing core.** Mostly PHP/Laravel or Node/TS. And **none** implement deal-grading /
   scoring / scam-floor — the heart of our app.

---

## Candidate scan (what the searches surfaced)

| Repo | Stars | Last commit | Stack | License | Verdict |
|------|-------|-------------|-------|---------|---------|
| jez500/**pricebuddy** (the example) | 943 | 2026-06 | PHP/Laravel/Filament/MySQL | NOASSERTION (custom) | 2/5 — URL-scrape + threshold alerts, no catalog/scoring/scam. Reference only |
| Cybrarist/**Discount-Bandit** | 693 | 2026-06-01 | PHP/Laravel | **none ⚠️** | Skip — best features but unlicensed + scraper-not-API + PHP |
| clucraft/**PriceGhost** | 572 | 2026-02-03 | TS (Node/React/Prisma) | **none ⚠️** | Skip — unlicensed, 4mo old, generic scraper |
| appstore-discounts | 396 | 2026-06-02 | TS | MIT | Skip — App Store only |
| SpikeHD/**AmazonMonitor** | 289 | 2026-05-08 | TS | GPL-3.0 | Skip — Amazon+Discord only, copyleft |
| driscoll42/ebayMarketAnalyzer | 258 | 2022-12 | Python | none ⚠️ | Abandoned, analysis-only (sold-listing medians) |
| Crinibus/scraper | 237 | 2025-01 | Python | MIT | Generic CLI multi-site scraper |
| ponyriders/django-amazon-price-monitor | 157 | 2019-05 | Python/Django | BSD-3 | **EOL 2019** — right stack, dead |
| reubenlavin08/**bullseye-app** | 4 | 2026-05-10 | Python | AGPL-3.0 | Read-don't-copy — best scoring + rate-limit design analog |
| Dacilla/**PCDealTracker** | 1 | 2026-05-20 | Python/**FastAPI**+SQLAlchemy+Alembic+Postgres | **MIT** | Near-identical stack; mine catalog/migration/reviewer patterns |
| MrAntonS/For-Gamers | 0 | 2025-12-29 | Py/Flask+TS, Postgres/Redis/Docker | none ⚠️ | Closest stack + **official eBay Buy API**, but unlicensed/Flask/gaming |
| traviszech/Ebay-Price-Scraper-w-Median | 0 | 2026-02-05 | Python | none ⚠️ | Closest domain (enterprise networking gear, quartile pricing) but scrape-based desktop |

⚠️ = no license → reference-only, cannot legally reuse code.

**Closed-source competitor:** hardwarehunter.io — same sources/categories (incl. ECC), scam scoring,
Telegram/email. SaaS. Confirms demand; OSS space is open.

---

## pricebuddy deep-dive (the user's example)

- **Stack:** PHP 8.4 / Laravel 12 / Filament 3 admin UI / MySQL 8.2; SeleniumBase Python scraper sidecar.
- **Model:** user adds product URLs + per-store extraction rules (CSS/XPath/Regex/JSONPath/Schema.org);
  Laravel scheduler scrapes daily (`0 6 * * *`); "deals" = per-product `notify_price`/`notify_percent`
  threshold vs first recorded price. **No** API integration, catalog, scoring, scam-floor, rate budget.
- **Notifications:** in-app, email, Pushover, Gotify, Apprise. **No Telegram** (Apprise can proxy), no digest.
- **Upstream health:** 943★, ~solo author, very active (v1.0.46 2026-03-29), custom non-OSI license.
- **Gives free:** price-history schema + Chart.js viz, Filament CRUD UI, notification-channel abstraction,
  scheduler skeleton, generic HTML scrape engine. (All the *easy* parts to build in FastAPI anyway.)
- **Verdict: 2/5 as a base.** Reference/inspiration only — wrong language, wrong paradigm, lacks every
  hard part of our app.

---

## PriceGhost deep-dive — code-level fork assessment (license set aside)

Sean rejected the license-based dismissal and asked for a real forkability call. A follow-up agent
cloned and read the source. Verdict: **don't fork — for architecture/stack reasons, not license.**

- **Real stack (corrected from the earlier skim):** Node/Express/**TypeScript**, **raw `pg` + hand-written
  SQL** (no Prisma/ORM; `database/init.sql`), React+Vite+recharts frontend, **Puppeteer-stealth** scraping,
  `node-cron`. **Zero automated tests.** Single author (clucraft), v1.0.6 dated 2026-01-26.
- **Crown jewel = the extraction engine** (`backend/src/services/scraper.ts`, 2,135 LOC): a genuine
  multi-strategy **confidence-voting** pipeline — `ExtractionMethod = json-ld | site-specific | generic-css
  | ai`; each emits `PriceCandidate{price,confidence}`; `findPriceConsensus()` (line 50) votes and falls
  back to **AI arbitration** on disagreement; `needsReview` surfaces to a human-disambiguation modal.
  BUT sources are **hardcoded `match:(url)=>/regex/` blocks** (Amazon/Walmart/eBay/Newegg) in one file —
  **no adapter interface**. The eBay handler (line 741) is **Puppeteer HTML scraping, NOT the Browse API**.
- **AI** (`ai-extractor.ts`): per-user provider switch (anthropic/openai/ollama/gemini); purpose is
  **price/stock extraction only** — no deal grade / scam / spec. **No OpenRouter**; cloud SDKs take apiKey
  only; **only the Ollama path has a configurable base URL** (so vLLM is reachable only by masquerading).
- **Data model:** 5 tables, **user-pinned-URL-centric** (`products(user_id, url UNIQUE, target_price,
  price_drop_threshold)`). **No catalog**, no `benchmark_median`/`scam_floor`, no item↔many-scored-listings.
- **Scheduling:** one `* * * * *` cron + 2–5s sleeps + jitter. **No API budget, no daily cap, no P0–P3 tiers.**
- **Notifications:** Telegram/Discord/ntfy/Gotify/Pushover. **No email, no digest, no per-channel score gate.**
- **Observability:** none (console.log).

**Requirement coverage: Met 2/10 (Docker, single-URL price-history+charts), Partial 2/10 (Telegram-only
notifs; AI extraction framework), Absent 6/10 — and the 6 absent are exactly our hard parts** (eBay API,
budget+tiers, scoring, scam-floor, catalog, adapter abstraction).

**Fork math:** out-of-box coverage ≈ **15–20%, all on the EASY surface** (UI, charts, notif fan-out, auth);
~**0% of the hard surface**. Forking forces rewriting our already-built Python eBay client + 4-layer rate
budget + scoring + scam-floor + 34-item catalog in TypeScript from scratch — i.e. deleting our highest-value
work to gain a generic URL scraper. The parts it gives free are 1–3 day items in FastAPI.

**Fork would only be right if ALL held (none do):** (1) committing to TS/Node anyway; (2) hadn't already
built the eBay/budget/scoring/catalog hard parts; (3) primary source was arbitrary-retailer HTML scraping,
not the eBay API. Our spec is eBay-API-first + curated scored catalog → the voting engine is peripheral
(Browse API already returns structured price/condition/seller) and the UI is cheap to rebuild.

**Steal-don't-fork (the real win):** when we reach feature-005's **Shopify-JSON-LD / PCPartPicker** adapters
(where HTML/JSON extraction actually matters), **port `findPriceConsensus` + the JSON-LD extractor
(`scraper.ts:50–237`) into a Python source-adapter (~1 day)** — captures the only real IP without the stack
switch. Optionally crib the recharts `PriceChart`/`Sparkline` components into our Next.js frontend.

Clone for reference: `/tmp/priceghost-eval` (key files: `backend/src/services/{scraper,ai-extractor,scheduler,notifications}.ts`, `backend/src/models/index.ts`, `database/init.sql`).

---

## Our project — baseline the agents established

- **~30% MVP2-ready**, but framework is solid: FastAPI async + Postgres + Redis + Next.js 15 + Docker;
  7 models; eBay OAuth Browse client + mock + parser + dedup + 4-layer RateBudgetManager; 6-component
  scoring engine + scam-floor; Telegram + email clients (implemented, were unwired).
- **feature-001 (keystone) 3/5 stories done** on `mega-feature-data-flow` worktree: config modernization,
  scoring-in-poll (ADR-006), APScheduler lifespan. Remaining: un-stub search endpoints, test suite.
- **Bespoke / hard-won (the moat):** 34-item curated catalog w/ researched `benchmark_median` + `scam_floor`
  (EPYC, workstation GPU, ECC RDIMM, enterprise NVMe/HDD, NICs, PSUs); domain-tuned scoring weights;
  eBay P0–P3 rate-budget design; multi-source adapter abstraction.
- **Generic / interchangeable:** CRUD, dashboard UI, Postgres schema, JWT auth, notification dispatch,
  Makefile/Docker.

---

## ACTIONABLE — patterns/building-blocks to fold in (legally clean)

> These are the *salvage value* of the fan-out. Tagged by likely milestone.

### For MVP2
- **[feature-001 / eBay client] `eBay/ebay-oauth-python-client`** (official eBay, MIT, Python, 100★).
  The one drop-in Python building block. **Action:** diff against our hand-rolled OAuth in
  `app/services/ebay/client.py` — adopt their app/user token-refresh handling if cleaner. Low effort.
- **[feature-004 / catalog] `Dacilla/PCDealTracker`** (MIT, FastAPI+SQLAlchemy+Alembic+Postgres).
  Near-identical stack. **Action:** mine their persisted "v2 catalog" pattern, Alembic migration layout,
  history/trends/filters endpoints, and especially the **`needs_review` manual match-decision reviewer
  workflow** — directly relevant to user-managed catalog CRUD + match confidence.

### For MVP2 feature-006 or MVP3
- **[feature-006 / price history + scoring] `reubenlavin08/bullseye-app`** (AGPL — **read, do NOT copy code**).
  Best design analog to our scoring + rate limiter. Key idea worth stealing conceptually: an **eBay Browse
  *sold/completed* comps pipeline** — Tukey-trimmed 90-day median + IQR — as the **historical baseline**,
  instead of only the static `benchmark_median`. **This fills the `_historical_stats_for(item)` seam we
  deliberately left returning `{}` in poller story-002.** Also: their 4-layer adaptive rate limiter
  (exponential cooldown + slow-start + half-open circuit breaker + round-robin) parallels our
  RateBudgetManager — compare designs. NOTE: AGPL is viral → reimplement from the idea, don't lift code.
- **[feature-005 / multi-source] `MrAntonS/For-Gamers`** (unlicensed — read-only).
  Uses the **official eBay Buy API** with "smart grouping" of listings per model (all "RTX 3080" together)
  + condition tagging (New/Used/Refurb). **Action:** review their grouping/condition-classification approach
  to inform per-catalog-item listing aggregation. Reference only (no license, Flask).
- **[notifications] Discount-Bandit + pricebuddy** — per-user notification *criteria* objects and the
  **Apprise** channel abstraction (bridges Telegram/email/100+ services). Idea reference for our dispatcher
  (feature-003) if we ever want >2 channels without bespoke clients.
- **[extraction] PriceGhost** — multi-strategy price extraction with **confidence voting** (JSON-LD → site
  scraper → CSS → AI arbitration). Idea reference for the Shopify JSON-LD adapter (feature-005) robustness.

### eBay building-block libraries (for reference / avoid)
- `hendt/ebay-api` (204★, MIT, TS, active) — most complete OAuth+Browse coverage; **wrong language**, best spec reference.
- `timotheus/ebaysdk-python` (851★) — **legacy Finding/Trading APIs, deprecated**; avoid for Browse work.
- `AverHLV/browseapi` (7★, MIT, 2019) — async Browse client; stale, code reference only.
- eBay MCP servers (adjacent): `hanku4u/ebay-mcp-server` explicitly targets "homelab deal hunting" w/ deal
  detection + price history + watchlist — worth a glance for feature ideas.

---

## One-paragraph recommendation (for the record)

Keep building on our FastAPI/Postgres codebase; the bespoke catalog + scoring + scam engine is the IP and
no mature OSS full-app exists in this niche. Treat every repo above as **reference-only**. The single
adoptable Python building block is `eBay/ebay-oauth-python-client`. The highest-value *idea* to fold in is
bullseye-app's eBay sold-comps historical baseline (feature-006), which plugs into the `_historical_stats_for()`
seam already stubbed in the poller. Re-evaluate only if a permissively-licensed Python eBay-API + catalog +
scoring app appears — none does today.
