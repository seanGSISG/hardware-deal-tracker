# Source Roadmap, eBay Call Ceiling & Growth Check (feature-003)

Operator-facing record of (1) which ingestion sources are live / deferred and why,
and (2) the eBay 5,000 calls/day ceiling and how to request more. Decisions trace
to **ADR-003** ("Shopify scored, PCPartPicker benchmark-only; defer Amazon /
Micro Center with a recorded go/no-go"). The full go/no-go rationale lives in the
mega-plan findings; this doc is the committed, in-repo summary.

## Source status (MVP3)

| Source | Status | Role | Notes |
|--------|--------|------|-------|
| eBay Browse API | **LIVE** | Scored deal feed | 5,000 calls/day ceiling (below). |
| Shopify retailers | **PARTIAL (3 of 6 live)** | Scored deal feed | **Re-verified live 2026-06-30** — the registry's 2026-06-02 verification had rotted. LIVE: TechMikeNY (only via `www.techmikeny.com` — apex now 404s), Cloud Ninjas, SaveMyServer (low-cadence price memory). DISABLED: UnixSurplus (`/products.json` now 404), ServerMonkey (now 403 bot-block), Natex (domain SERVFAIL/dead). Per-source robots/ToS gate + own rate bucket. See `SOURCE_ONBOARDING.md` + re-verification note below. |
| PCPartPicker | **OFF (gated)** | New-retail benchmark only | Never scored; residential egress + circuit breaker. See `PCPARTPICKER_EGRESS.md` + `PCPP_MAPPING.md`. |
| Amazon PA-API | **DEFERRED (NO-GO MVP3)** | (future) new-retail benchmark | Associates affiliate-sales quota gate. See below. |
| Micro Center | **NOT MONITORED (NO-GO, re-probed 2026-08-26)** | (future) regional benchmark | No public API. Cloudflare managed challenge on every path incl. `/robots.txt`; 403 to curl and to a desktop UA. No compliant server-side route. See below. |

## Shopify re-verification — 2026-06-30 (operator action: enablement)

`ENABLE_SHOPIFY_SOURCES` had never been set in the deployed `.env`, so Shopify
ingestion was silently **off** (config default is `False`). It was turned on this
date. A live probe of each store's `/products.json` from the host showed the
2026-06-02 registry verification had drifted:

| Store | products.json (2026-06-30) | Action |
|-------|----------------------------|--------|
| techmikeny | apex 404, **`www.` → 200** | LIVE via `SHOPIFY_TECHMIKENY_BASE_URL=https://www.techmikeny.com` |
| cloud_ninjas | 200 | LIVE |
| savemyserver | 200 | LIVE (price-memory cadence) |
| unixsurplus | 404 (endpoint removed) | `SHOPIFY_UNIXSURPLUS_ENABLED=false` |
| servermonkey | 403 (bot-block) | `SHOPIFY_SERVERMONKEY_ENABLED=false` |
| natex | 000 (domain SERVFAIL) | `SHOPIFY_NATEX_ENABLED=false` |

Flags live in `project/.env` and are forwarded through the backend
`environment:` allowlist in `docker-compose.yml` (the service does **not** use
`env_file:`, so every new setting must be added there to reach the container).
The 3 live adapters fetch 750 products/store; 0 catalog matches at enablement is
expected (strict per-SKU keyword match; none of the 34 tracked models in stock).

**Follow-up (re-onboard the 3 disabled stores):** find UnixSurplus's current
catalog endpoint (or drop it), get past ServerMonkey's bot-block compliantly (or
drop it), and confirm whether Natex moved domains or shut down. Then flip the
per-store `*_ENABLED` flags back on.

## Amazon PA-API — NO-GO for MVP3 (reconsider MVP4)

PA-API 5.0 access is tied to an **Amazon Associates** account that must generate
**qualifying affiliate sales** to keep its request quota; new accounts get a small
quota that is **revoked if no sales occur within ~180 days**, and throttling
scales with sales volume. A price tracker with no storefront cannot reliably keep
credentials provisioned, so PA-API is an unstable foundation today. **Unblock
path (MVP4):** stand up an affiliate-link surface (e.g. "buy on Amazon" CTAs)
producing qualifying sales, then add Amazon as a *new-retail benchmark* source
(reference-only, like PCPartPicker) — not a scored deal feed.

## Micro Center — NO-GO for MVP3, re-probed and still NO-GO (2026-08-26)

No public API, strong anti-bot protection, and **store-/region-scoped, often
in-store-only** pricing that doesn't map onto a national ship-anywhere catalog.
**Reconsideration trigger (MVP4):** an official feed/API or a compliant aggregator;
if revived it would be a **regional new-retail benchmark** behind the same
residential-egress + circuit-breaker posture, never a scored hot-deal feed.

### Re-probe 2026-08-26 (measured, from the Spark host egress)

Sean asked for Micro Center coverage on the Arc Pro B70 watch. Probed directly
rather than trusting the 2026-06-02 record — the posture has if anything hardened:

| Path | Result |
|------|--------|
| `GET /robots.txt` | **Cloudflare managed challenge** (`Just a moment...`, `cf_chl_opt`) — their crawl policy is itself unreadable without solving the challenge |
| `GET /search/search_results.aspx?Ntt=arc+pro` | **403** |
| `GET /sitemap.xml` | **403** |
| `GET /product/<id>/x.aspx` | **403** |
| `HEAD /` as `curl/8.5.0` | **403** |
| `HEAD /` as a desktop-Chrome UA | **403** |

There is no unauthenticated server-side path to Micro Center pricing from a
datacenter IP. The site does answer a **Googlebot user-agent with 200**, but
spoofing a search-engine UA to defeat a bot-block is user-agent spoofing /
detection evasion — **deliberately not implemented, and not to be implemented.**

### Compliant options, if Micro Center coverage is wanted

1. **Slickdeals RSS as a proxy signal** — `slickdeals.net/newsearch.php?q=<terms>&searcharea=deals&searchin=first&rss=1`
   returns **200 with 25 items**, no anti-bot, and carries Micro Center deals
   (incl. their PowerSpec house brand). Catches *posted* MC deals, misses quiet
   price drops. Would be a new `sources/` adapter with its own rate bucket, and
   **benchmark-only** — Slickdeals prices are user-submitted and unverified.
2. **Residential-egress browser fetch** — reuse the exact posture already built
   for PCPartPicker (`PCPARTPICKER_EGRESS.md`): a real browser on Sean's own
   residential connection (cachy / thepower), his own session, low cadence,
   circuit breaker. This is the only route that sees true store-scoped MC pricing.
3. **Do nothing automated** — Micro Center pricing is store-local and Sean is
   in-store range of one; a manual check beats a fragile scraper.

Nothing here is wired up: **Micro Center is currently NOT monitored.** Picking
between (1) and (2) is a design decision, tracked as an idea rather than assumed.

## eBay 5,000 calls/day ceiling

The eBay Browse API application token is capped at **5,000 calls/day** by default
(`EBAY_DAILY_CALL_LIMIT=5000`). The poller stays under it with:

- **A 4-tier `RateBudgetManager`** (`app/services/ebay/rate_budget.py`): each
  tracked item has a poll interval that maps to a priority **P0 (hot, ~5 min) →
  P3 (passive, ~30 min)**. Higher tiers poll more often; lower tiers rarely.
- **A near-limit threshold** (`EBAY_NEAR_LIMIT_THRESHOLD=4000`): once the daily
  count crosses it, only **P0** searches are allowed — non-critical polling backs
  off so the day never blows the cap.
- **A safety buffer** (`EBAY_CALL_BUFFER=200`) reserved below the hard cap.
- **One call per item poll** (the Browse search), so the daily budget ≈ the number
  of item-polls/day across all tiers; tier intervals are tuned to land under 4,800
  effective calls/day.
- **Non-eBay sources never touch this budget** — every Shopify source and
  PCPartPicker uses its **own** `SourceRateBudget` bucket (ADR-003).

If the catalog or poll cadence grows, the 5,000/day cap can be raised:

### eBay Application Growth Check (raising the allocation)

The default 5,000 calls/day is the **pre-approval** tier. To get a higher daily
call allocation, an application must pass eBay's **Application Growth Check**:

1. In the **eBay Developers Program** portal, open your application/keyset and find
   the **Application Growth Check** (a.k.a. "Compatible Application Check" /
   call-limit increase request) under the app's API call-limit settings.
2. eBay reviews the application for **policy/ToS compliance** and that it provides
   legitimate value to buyers/sellers (proper attribution, no prohibited use of
   data, correct affiliate/marketplace handling).
3. On approval, the app is moved off the default tier to a **higher per-day call
   allocation** (commonly into the hundreds-of-thousands/day range), and limits
   then scale with demonstrated, compliant usage.

**Operator action when approaching the ceiling:** before requesting an increase,
first confirm the tiered budget is tuned (intervals, P0/P3 distribution) so the
increase is genuinely needed; then submit the Growth Check from the developer
portal. After approval, bump `EBAY_DAILY_CALL_LIMIT` (and the near-limit/buffer)
to match the new allocation.
