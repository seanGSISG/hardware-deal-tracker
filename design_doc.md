# Technical Design: Hardware Deal Tracker — MVP2
> Level: project | Components: 7 | Patterns: 5 | ADRs: 9
## Overview
FastAPI + Next.js app that polls marketplaces for enterprise/workstation hardware deals, scores them, and notifies. MVP2 makes the data flow real (scheduler + poller + scoring + dashboard), wires notifications and locks down auth, hardens build/CI/image hygiene, and adds price history, AI deal analysis, observability, multi-source ingestion, and a user-managed catalog that works from an empty database.
### Goals
- A scheduled poll cycle ingests, scores, and persists listings that render in the dashboard
- Hot deals dispatch Telegram + email (instant) and digest (daily/weekly)
- Registration is closed by default; app refuses to boot with a placeholder SECRET_KEY
- make test green in GitHub Actions on every PR; backend prod image <300MB; idempotent seed
- Price history + trend charts let a user judge a price against its own history
- AI deal grade + scam signal + spec extraction over listing text (configurable OpenRouter/vLLM)
- Prometheus/Grafana observability of poll/scoring/rate-budget/errors
- Pluggable multi-source ingestion (eBay first; researched US sources + Micro Center next)
- Full user-managed catalog CRUD; the app operates correctly from a fresh/empty catalog
### Non-Goals
- paperless (MVP3 at earliest)
- Photo/vision AI analysis
- SSO / Authentik / Entra integration (not selected for MVP2)
- pgvector, multi-origin CORS, httpOnly cookie session (deferred behind Tailscale + CF Access)
- eBay Application Growth Check / higher rate caps
## Architecture
Next.js 15 frontend -> FastAPI backend (JWT auth) -> Postgres 17 + Redis 7. An in-process APScheduler (AsyncIOScheduler) in the FastAPI lifespan ticks the poller; the poller fans out across source adapters (eBay first), normalizes + dedups listings, scores them via DealScoringEngine (benchmark from the catalog), optionally enriches them via the AI analysis service, persists listings + scores + price-history points, then the NotificationDispatcher fans scored deals to Telegram/email per-user thresholds (instant) with a separate digest job. Prometheus metrics are exposed at /metrics. n8n is removed.
### Components
#### Scheduler (APScheduler v3 in lifespan)
AsyncIOScheduler started in app/main.py lifespan; IntervalTrigger _poll_tick wrapper opens its own session and runs poller.search_all(db).
- Responsibilities: tick the poller on POLL_SCHEDULER_INTERVAL, run the notification digest job, record price-history snapshots, clean shutdown on SIGTERM
- Dependencies: Poller, NotificationDispatcher, PriceHistory

#### SourceAdapter abstraction
Common interface search(catalog_item) -> normalized listing dicts; EbayBrowseClient/EbayPoller refactored into the first adapter; additional US sources added per research.
- Responsibilities: normalize listings to a shared shape, respect per-source rate limits + ToS, expose source identity on each listing
- Dependencies: RateBudgetManager, DeduplicationEngine

#### DealScoringEngine
6-component scoring; benchmark read from the catalog (TrackedItem), not a hardcoded dict.
- Responsibilities: score a listing against its catalog benchmark + history, expose score components
- Dependencies: HardwareCatalog

#### AI Analysis Service
Configurable provider (OpenRouter default / local vLLM opt-in); NL deal grade, scam signal, spec extraction.
- Responsibilities: enrich listings with AI verdict/flags/specs, degrade gracefully when provider down, bound cost/latency
- Dependencies: Listing, HardwareCatalog

#### NotificationDispatcher
Fans scored deals to Telegram/email per-channel thresholds; digest job for non-instant email.
- Responsibilities: per-channel gating (telegram_min_score/email_min_score/mute_until), isolate channel failures, batch digests
- Dependencies: TelegramClient, EmailClient, NotificationSetting

#### Catalog + CRUD
HardwareCatalog as source of truth; generate_seed.py emits SQL; admin CRUD API + UI; empty-DB capable.
- Responsibilities: single source of truth for tracked items, user create/edit/delete, no hard dependency on seed data
- Dependencies: TrackedItem

#### Observability (Prometheus/Grafana)
/metrics exporter + committed Grafana dashboard JSON.
- Responsibilities: instrument poll/scoring/rate-budget/errors/tick-duration
- Dependencies: Scheduler, Poller, RateBudgetManager

### Patterns
- **Adapter**: SourceAdapter interface for each marketplace. — _Add sources without touching the scheduler/scoring/notification core._
- **Dependency Injection (FastAPI Depends)**: get_db / get_current_user injected into endpoints. — _Testable, consistent session + auth handling._
- **Strategy (AI provider)**: Pluggable LLM provider selected by env. — _OpenRouter default, local vLLM opt-in without code changes._
- **Outbox-lite dispatch with isolation**: Each notification channel wrapped in try/except+log. — _One failing channel never sinks the others._
- **Single source of truth (catalog)**: Python HardwareCatalog generates seed SQL; benchmark read from catalog. — _Kills drift between three copies of the 34 items._

### Data Flow
scheduler tick -> poller.search_all -> per source adapter.search -> normalize -> dedup -> score (catalog benchmark) -> [optional AI enrich] -> persist listing+score+price-point -> dispatcher.dispatch_for_deal -> Telegram/email; digest job rolls up deferred email deals; dashboard reads listings/scores/price-history/AI results.
## Interfaces
### Data Models
#### NormalizedListing
| Field | Type |
|-------|------|
| title | - |
| price | - |
| shipping | - |
| total | - |
| condition | - |
| url | - |
| source | - |
| seller | - |
| raw_payload | - |

#### NotificationSetting
| Field | Type |
|-------|------|
| telegram_enabled | - |
| telegram_min_score | - |
| telegram_chat_id | - |
| email_enabled | - |
| email_min_score | - |
| email_address | - |
| email_digest_mode | - |
| mute_until | - |

## Architecture Decisions
### ADR-001: In-process APScheduler v3 (AsyncIOScheduler), not v4 [accepted]
- **Context**: Need scheduled polling; APScheduler v4 is still alpha (4.0.0a6).
- **Decision**: Pin apscheduler>=3.11.2,<4 and use the v3 API inside a FastAPI lifespan with coalesce=True, max_instances=1, replace_existing=True.
- **Rationale**: Stable API; coalesce/max_instances prevent thundering-herd after downtime and overlap; lifespan replaces deprecated on_event.
- **Alternatives Considered**: APScheduler v4 alpha, external worker (Celery/Prefect), keep n8n for scheduling

### ADR-002: Dependency-driven parallel execution; drop serial-phase rule [accepted]
- **Context**: MVP2.md mandated 'phases run in order, not in parallel'; Sean explicitly removed it.
- **Decision**: Order work only by real dependencies; run independent features in isolated git worktrees concurrently. Correctness comes from per-story quality gates (TDD, code review, adversarial verify), not roadmap serialization.
- **Rationale**: Faster throughput without the MVP1 quality regression, because gates are per-story now.
- **Alternatives Considered**: keep strict serial phases, single shared branch

### ADR-003: SourceAdapter abstraction; PCPartPicker = priority source #2, Shopify JSON-LD follow-on [accepted]
- **Context**: MVP2 adds sources beyond eBay. Sean's directive: source #2 is our OWN PCPartPicker scraper (study pypartpicker / N-O-U-R / docyx repos), used mainly as a price-benchmark/reference for the consumer-adjacent catalog overlap. Used-server-retailer research (plan/MVP2_SOURCE_RESEARCH.md) found most run Shopify with public /products.json + JSON-LD.
- **Decision**: Introduce a SourceAdapter interface; refactor eBay into the first adapter. Source #2 = PcPartPickerAdapter (our own; reuse pypartpicker's data model, replace its stale transport; see plan/MVP2_PCPARTPICKER_RESEARCH.md). It is a BENCHMARK/REFERENCE source ONLY (refresh benchmark_median + 'vs retail' delta) -- NOT a deal-listing feed; never routed through the eBay scoring/dedup/notification pipeline. Scoped to the ~10-12 overlapping consumer-adjacent catalog items (workstation GPU, consumer NVMe/SSD, non-ECC DDR, Threadripper) via optional pcpp_product_id; useless for EPYC/ECC-RDIMM/enterprise HDD/server boards. Anti-bot cheapest-first ($0/mo target, ~10-12 pages/day), env-configurable: curl_cffi TLS-impersonation + caching -> RESIDENTIAL Tailscale exit (NOT datacenter 104.223.27.177) -> Nodriver/FlareSolverr for clearance cookies -> paid API (Zyte/Bright Data) behind a flag last. Own <=200/day bucket, ENABLE_PCPARTPICKER=false default, circuit-breaker on Cloudflare. HEAVY ToS caveat: PCPartPicker forbids scraping + has no public API -- minimal volume, cache, never redistribute, keep disableable. Source #3+ = generic ShopifyJsonLdAdapter (TechMikeNY > UnixSurplus > ServerMonkey). Persist source + source_listing_id; dedup on (source, source_listing_id); per-source rate-budget buckets (NOT eBay's 5000/day). DEFER Amazon PA-API and Micro Center to MVP3. Verify platform + robots.txt/ToS per site before coding each adapter.
- **Rationale**: PCPartPicker gives broad current-retail price signal for the consumer-overlap catalog (sharper benchmarks/'vs retail' deltas); Shopify JSON-LD is the lowest-ToS-risk used-server polling target; the adapter pattern adds sources without touching the scheduler/scoring/notification core. Keep scraping cheap via self-hosted infra before paid APIs.
- **Alternatives Considered**: eBay-only with copy-paste clients, Shopify retailers as source #2 (demoted to #3+), bespoke HTML scrapers per site, paid scraping API first, Amazon/Micro Center first

### ADR-004: Configurable AI provider (OpenRouter default, local vLLM opt-in) [accepted]
- **Context**: AI deal analysis chosen; Sean wants both cloud and self-hosted.
- **Decision**: Strategy pattern selected by env (AI_PROVIDER); OpenRouter (Gemini 2.5 Flash primary, Qwen 3.6 Plus/GPT-4o-mini fallback) default, local vLLM on DGX Spark opt-in. Text-only (no vision). Graceful degradation when provider down.
- **Rationale**: Honors native/self-hosted preference while keeping a zero-setup default; AI stays optional.
- **Alternatives Considered**: OpenRouter only, local vLLM only, no AI

### ADR-005: App must operate from an empty catalog; seed is optional [accepted]
- **Context**: Sean wants to eventually bootstrap fully from a fresh database via UI.
- **Decision**: Treat the 34 seeded items as optional starter data. No code path may assume tracked items exist; full CRUD lets users build the catalog from zero. A test boots with zero items and asserts graceful behavior.
- **Rationale**: Enables fresh-DB bootstrap and prevents hidden seed coupling.
- **Alternatives Considered**: seed required at boot, read-only curated catalog

### ADR-006: Wire scoring into the poll path [accepted]
- **Context**: The poller currently ingests+dedups but never calls the scoring engine.
- **Decision**: Call DealScoringEngine in search_item and persist the score, so listings render scored and the dispatcher has scores to gate on.
- **Rationale**: Required for the Phase 01 dashboard exit criterion and for notifications; closes a gap not in the written plan.
- **Alternatives Considered**: score lazily on dashboard read, separate scoring sweep job

### ADR-007: Remove n8n from the stack [accepted]
- **Context**: n8n was the original external automation/scheduler; superseded by in-process APScheduler.
- **Decision**: Delete the n8n service + volume from compose, drop N8N_* env, update README; tear down on docker-host-01.
- **Rationale**: Fewer moving parts; scheduling now lives in the backend.
- **Alternatives Considered**: pin + healthcheck n8n, keep n8n for future workflows

### ADR-008: Per-channel notification thresholds (no single alert_threshold) [accepted]
- **Context**: Plan text referenced alert_threshold; the model actually uses per-channel scores.
- **Decision**: Dispatcher gates each channel independently on telegram_min_score(70)/email_min_score(50), honors mute_until, and emails to NotificationSetting.email_address.
- **Rationale**: Matches the real model; lets users tune channels separately.
- **Alternatives Considered**: single global threshold

### ADR-009: Migrate config to Pydantic v2 SettingsConfigDict + fail-loud SECRET_KEY [accepted]
- **Context**: config.py uses deprecated class Config; SECRET_KEY silently defaults to a placeholder.
- **Decision**: feature-001 migrates config to model_config = SettingsConfigDict and owns config.py; feature-003 adds a boot-time RuntimeError when SECRET_KEY is the placeholder/unset and removes the compose default.
- **Rationale**: Kills deprecation warnings and prevents shipping a known dev secret.
- **Alternatives Considered**: leave placeholder, warn-only

## Story Mappings
| Story | Components | Decisions | Interfaces |
|-------|-----------|-----------|------------|
| feature-001 | Scheduler (APScheduler v3 in lifespan), SourceAdapter abstraction, DealScoringEngine | ADR-001, ADR-006, ADR-009 | - |
| feature-002 | Observability (Prometheus/Grafana), Scheduler (APScheduler v3 in lifespan) | ADR-007 | - |
| feature-003 | NotificationDispatcher | ADR-008, ADR-006, ADR-009 | - |
| feature-004 | Catalog + CRUD, DealScoringEngine | ADR-005 | - |
| feature-005 | SourceAdapter abstraction | ADR-003 | - |
| feature-006 | AI Analysis Service, Catalog + CRUD | ADR-004 | - |
