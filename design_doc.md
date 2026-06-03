# Technical Design: Hardware Deal Tracker — MVP3 (harden + surface)
> Level: project | Components: 7 | Patterns: 5 | ADRs: 7
## Overview
Turn the working MVP2 backend into a polished, production-leaning product: surface every backend capability in the established dark-terminal UI, move auth server-side, deepen scoring with real eBay sold-comps, bring deferred sources online, and clear the quality/ops backlog.
### Goals
- Surface price history, AI analysis, multi-source listings, and observability in the existing monospace/amber UI — build-verified.
- Server-side auth (httpOnly cookie + Next middleware) with multi-origin CORS.
- Real market-history scoring via eBay sold-comps (fill the _historical_stats_for seam).
- Onboard Shopify retailer adapters live; make PCPartPicker runnable behind a residential egress flag.
- Strict CI lint, modern password hashing, correct categories, fresh docs, live-creds smoke.
### Non-Goals
- Redesigning the frontend visual language (it is authoritative — extend only).
- Shipping Amazon PA-API or Micro Center (evaluate + record go/no-go for MVP4).
- Routing PCPartPicker rows through scoring/notifications (benchmark-only).
- Making semantic/pgvector matching mandatory (stretch, flagged).
## Architecture
FastAPI + async SQLAlchemy + Postgres + Redis backend with an APScheduler poll loop feeding a SourceAdapter abstraction (eBay + Shopify + PCPartPicker-benchmark), a 6-component scoring engine, a notification dispatcher, and a configurable AI analyzer; a Next.js 15 App Router frontend in a dark monospace/amber design system. MVP3 adds a sold-comps baseline service, server-side session auth, live multi-source ingestion, and a frontend surfacing layer, plus an optional pgvector semantic matcher.
### Components
#### ScoringBaselineService
Computes and persists a rolling per-item market-history baseline (Tukey-trimmed 90d median + IQR + stats) from eBay sold-comps or accumulated PriceHistory; fills EbayPoller._historical_stats_for().
- Responsibilities: fetch/aggregate sold comps, trim + compute median/IQR/stats, persist rolling snapshot, degrade to catalog benchmark
- Dependencies: DealScoringEngine, PriceHistory, EbayBrowseAdapter

#### AuthSession
Server-side session: httpOnly Secure cookie issuance/clearing on the backend + Next.js middleware route protection; bearer flow preserved for API/tests; multi-origin CORS.
- Responsibilities: set/clear session cookie, validate cookie or bearer, middleware route guard, CORS allowlist
- Dependencies: get_current_user, Next middleware

#### SourceAdapter (extended)
Live Shopify JSON-LD adapters + PCPartPicker benchmark adapter with per-source rate buckets and cross-source dedup.
- Responsibilities: per-source fetch/normalize, per-source rate budget, dedup on (source, source_listing_id), robots/ToS gating
- Dependencies: RateBudgetManager, DeduplicationEngine

#### QualityGate/CI
Strict ruff lint (blocking), modern password hashing, correct eBay categories, fresh docs, creds-gated live smoke.
- Responsibilities: lint backlog cleanup, bcrypt/argon2 hashing, category correctness, doc refresh, live smoke
- Dependencies: GitHub Actions, pyproject ruff config

#### FrontendDesignSystem
The authoritative dark monospace/amber component language; MVP3 extends it to surface listings, price-history, AI analysis, source badges, digest settings, and observability. Every change is gated by a passing next build.
- Responsibilities: reuse lib/api.ts + existing components, LIVE LISTINGS/HISTORY/AI panels, toast wiring, settings + dashboard surfacing, next build verification
- Dependencies: recharts, sonner, lib/api.ts

#### SemanticMatcher
Optional pgvector-backed embedding similarity for listing->catalog attribution and similar-items; flagged + degrades gracefully.
- Responsibilities: embed catalog/listings, cosine similarity ranking, suggest catalog match
- Dependencies: pgvector, AIClient embeddings

#### CommunitySignalSource
Distinct ingestion class for unstructured peer-to-peer deal posts (Reddit r/homelabsales, STH); AI-extracts structured fields into a LEADS surface, separate from the scored-listing pipeline. Gated.
- Responsibilities: pull community posts (Reddit OAuth/STH), AI free-text extraction, sold/traded filter + dedup, leads table/endpoint
- Dependencies: AIClient, RateBudgetManager

### Patterns
- **Graceful degradation**: Sold-comps, AI, and semantic matching all fall back cleanly when data/creds/providers are absent. — _Core app must always run (incl. empty DB, AI off)._
- **SourceAdapter + per-source rate buckets**: Each source has its own fetch/normalize + polite rate budget; dedup on (source, source_listing_id). — _Add sources without touching the scoring core or eBay budget._
- **Server-side session**: httpOnly cookie + Next middleware; bearer retained for API/tests. — _Remove XSS-readable token + dashboard flash._
- **Design-system reuse**: All new UI reuses the monospace/amber components + lib/api.ts; no redesign. — _Consistency + the existing screenshots are the spec._
- **Build-verified frontend**: Every frontend change runs npm install && next build before completion. — _MVP2 frontend was never compiled._

### Data Flow
poll tick -> SourceAdapter(s) fetch/normalize -> dedup (source, source_listing_id) -> persist Listing -> ScoringBaselineService supplies historical stats -> DealScoringEngine scores -> persist ListingScore + PriceHistory point -> NotificationDispatcher (gated) -> AIAnalyzer (gated) -> frontend surfaces listings/score/history/AI in the design system; auth is enforced server-side via cookie+middleware.
## Interfaces
### Data Models
## Architecture Decisions
### ADR-001: Sold-comps baseline fills the scoring seam [accepted]
- **Context**: _historical_stats_for() returns {} so scoring uses only static benchmark_median.
- **Decision**: Compute a rolling 90d Tukey-trimmed median + IQR from eBay sold/completed comps (or accumulated PriceHistory when sold comps are unavailable to the app token), persist it, and feed DealScoringEngine; degrade to catalog benchmark when insufficient.
- **Rationale**: Scores reflect real market history; reuses the dict shape the engine already consumes.
- **Alternatives Considered**: keep static benchmark, third-party price API

### ADR-002: Server-side auth via httpOnly cookie + Next middleware [accepted]
- **Context**: MVP2 auth is client-side localStorage with a flash-of-dashboard.
- **Decision**: Issue JWT in an httpOnly Secure SameSite cookie; protect routes in Next middleware; keep bearer for API/tests; multi-origin CORS allowlist.
- **Rationale**: Removes XSS-readable token and the redirect flash; lab + localhost origins.
- **Alternatives Considered**: keep localStorage, full session store

### ADR-003: Shopify scored, PCPartPicker benchmark-only [accepted]
- **Context**: Built adapters are dormant.
- **Decision**: Route Shopify JSON-LD listings through the normal score/persist/notify path with per-source rate buckets; keep PCPartPicker benchmark-only behind ENABLE_PCPARTPICKER + a residential Tailscale egress; defer Amazon/Micro Center with a recorded go/no-go.
- **Rationale**: Shopify rows are real deals; PCPartPicker is reference-only and ToS-sensitive.
- **Alternatives Considered**: score everything, scrape eBay HTML

### ADR-004: Strict CI lint + modern hashing [accepted]
- **Context**: ~143 legacy ruff violations left CI lint non-blocking; passlib is unmaintained.
- **Decision**: Clear the lint backlog and make ruff blocking in CI; migrate to bcrypt/argon2 with verify+rehash-on-login; correct HDD/SSD eBay categories.
- **Rationale**: Production hygiene + reproducibility.
- **Alternatives Considered**: keep lint advisory, stay on passlib

### ADR-005: Frontend design system is authoritative + build-verified [accepted]
- **Context**: Existing screenshots define the look; MVP2 frontend was never compiled.
- **Decision**: Extend the dark monospace/amber system (reuse lib/api.ts + components); no redesign; every frontend story must pass npm install && next build.
- **Rationale**: Consistency + catch the build breakage MVP2 deferred.
- **Alternatives Considered**: restyle, skip build verification

### ADR-006: Semantic matching is optional (pgvector), flagged [accepted]
- **Context**: Listing->catalog attribution could use embeddings.
- **Decision**: Add pgvector + embedding similarity behind a flag that degrades gracefully; never required for the core app.
- **Rationale**: Nice-to-have; must not add a hard dependency.
- **Alternatives Considered**: keyword-only matching, external vector DB

### ADR-007: Community signal is a leads pipeline, not scored listings [accepted]
- **Context**: Reddit r/homelabsales + STH posts are unstructured free text, fast-moving, high signal-to-noise.
- **Decision**: Build a separate gated CommunitySignalSource that AI-extracts fields into a LEADS surface with its own rate bucket + sold/traded filter; do NOT route through scoring/notifications. May slip to MVP4.
- **Rationale**: Different data shape + risk profile than structured price polling; keep the scored pipeline clean.
- **Alternatives Considered**: treat as a normal adapter, skip entirely

## Story Mappings
| Story | Components | Decisions | Interfaces |
|-------|-----------|-----------|------------|
| feature-001 | ScoringBaselineService | ADR-001 | - |
| feature-002 | AuthSession | ADR-002 | - |
| feature-003 | SourceAdapter (extended) | ADR-003 | - |
| feature-004 | QualityGate/CI | ADR-004 | - |
| feature-005 | FrontendDesignSystem | ADR-005, ADR-002 | - |
| feature-006 | SemanticMatcher | ADR-006 | - |
| feature-007 | CommunitySignalSource | ADR-007 | - |
