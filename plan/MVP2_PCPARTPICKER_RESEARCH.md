# MVP2 — PCPartPicker Price Source Research

> Research date: 2026-06-02. Goal: evaluate building our own PCPartPicker
> price scraper/adapter for the Hardware Deal Tracker, and decide whether/how it
> fits a catalog built around **used enterprise gear** (EPYC, server GPUs, ECC
> RDIMM, enterprise HDD, server boards).
>
> TL;DR recommendation: **Use PCPartPicker as a low-frequency price *benchmark/
> reference* source for the ~10-12 catalog items that are genuinely consumer/
> prosumer parts (workstation GPUs, consumer NVMe/SSD, some DDR, Threadripper),
> NOT as a live deal-listing source.** Build a thin `PcPartPickerAdapter` behind
> a shared `SourceAdapter` interface, run it on a slow cadence (daily/weekly) in
> its own rate bucket. Start cheapest-first: polite rate-limited requests via
> `curl_cffi` (TLS impersonation), escalate to a self-hosted FlareSolverr /
> Camoufox + our own homelab/Tailscale residential-ish egress only if blocked,
> and treat paid scraping APIs (ScraperAPI/Zyte/Bright Data) as a last resort.
> Heavy ToS caveat: PCPartPicker's ToS explicitly forbids scraping and price
> collection — keep volume tiny, cache aggressively, and treat this as a
> best-effort enrichment source that can be disabled.

---

## 1. Repo review

### lucwl/pypartpicker (Python wrapper) — the main candidate
- **Repo / PyPI:** https://github.com/lucwl/pypartpicker · https://pypi.org/project/pypartpicker/
- **Language:** Python. Current version **2.0.5, released 2024-12-28** (so ~18 months stale as of mid-2026, but the most recently touched of the wrappers).
- **Approach:** HTML scrape of rendered PCPartPicker pages. Parses product pages, part lists (`/list/<id>`), and the built-in search. It is *not* hitting a clean JSON API — it parses server-rendered HTML.
- **API surface (2.x):**
  - `Client()` / `AsyncClient()` with options: `max_retries` (default 3), `retry_delay`, `cookies`, `response_retriever` (custom request fn — the hook for proxy rotation), `no_js` (disables pyppeteer JS rendering).
  - `get_part(url_or_id, region)` -> `Part` (full data: `name`, `type`, `image_urls`, `url`, `cheapest_price`, `in_stock`, `vendors[]`, `rating`, `specs{}`, `reviews[]`).
  - `get_part_list(url_or_id, region)` -> `PartList` (`parts[]` partial, `estimated_wattage`, `total_price`, `currency`).
  - `get_part_search(query, page, region)` -> `PartSearchResult` (`parts[]`, `page`, `total_pages`).
  - reviews fetch -> `PartReviewsResult`.
  - Types: `Part`, `PartList`, `PartSearchResult`, `Price` (`base`, `discounts`, `shipping`, `tax`, `total`, `currency`), `Vendor`, `Rating`, `Review`, `User`.
  - Exceptions: **`CloudflareException`** (raised after max retries hit Cloudflare), **`RateLimitException`** (PCPP rate limit). The library *knows* it gets blocked — these exceptions are the tell.
  - Source: https://github.com/lucwl/pypartpicker
- **Anti-bot handling:** Ships "scraping countermeasures out of the box via `requests-html`", and uses **pyppeteer** (bundled Chromium) for JS rendering on first use unless `no_js=True`. The `response_retriever` callable is the intended extension point to plug in proxies / `curl_cffi` / a custom session. It does **not** solve Turnstile or run a maintained stealth browser.
- **Does it still work in 2026?** Partially / unreliably. The architecture is sound (it exposes exactly the fields we want, including per-`Vendor` pricing), but pyppeteer-class headless and plain `requests-html` are exactly what Cloudflare flags now (per Scrapfly 2026, puppeteer-stealth was deprecated Feb 2025 and undetected-chromedriver is "easily detected"). Expect `CloudflareException`/403 from datacenter IPs without help. **Reuse the data model and the `response_retriever` hook; do NOT trust its default transport.**
  - Cloudflare reality check: https://scrapfly.io/blog/posts/how-to-bypass-cloudflare-anti-scraping

### N-O-U-R/PcPartPicker-Scraping
- **Repo:** https://github.com/N-O-U-R/PcPartPicker-Scraping (last meaningful activity ~2024-05)
- **Language:** **Node.js.**
- **Approach:** Per-category scripts (`scrape_cpus.js`, `scrape_gpus.js`, …) that scrape category list pages *and* drill into each product's spec page, output to CSV (`gpus_detailed.csv`, etc.). Covers GPUs, PSUs, cases, CPUs, coolers, memory, storage, motherboards. ~90% extraction accuracy claimed.
- **Anti-bot handling:** Relies entirely on the **ZenRows paid scraping API** to render JS and bypass anti-bot — there is no self-hosted bypass logic. (README literally says "Don't try the API keys useless (;".)
- **Reuse vs stale:** The CSS selectors / category→field mapping are a useful *reference* for what's on each page, but the whole thing is welded to ZenRows and is in JS, not our stack. **Low reuse.** Mainly confirms "paid API renders JS, parse the HTML" works.

### docyx/pc-part-dataset (static dataset)
- **Repo:** https://github.com/docyx/pc-part-dataset
- **Language:** TypeScript (Puppeteer + puppeteer-cluster). **Static dataset, not a live scraper.**
- **Approach:** `src/scraper.ts` drives Puppeteer over PCPartPicker category pages (`ALL_ENDPOINTS`), stages JSON, then `src/output.ts` emits JSON/JSONL/CSV; `serialization-map.json` normalizes PCPP field names to stable keys. Includes `price` (or `null` when absent).
- **Coverage:** broad consumer catalog — cpu, cooler, motherboard, memory, internal/external storage, video-card, case, psu, OS, monitor, sound/network cards, peripherals, fans, thermal compound, UPS.
- **Maintenance:** **Last data refresh 2024-05-14; updates are manual, not automated.** Prices are point-in-time and now ~2 years stale.
- **Reuse:** Excellent for a **one-time bootstrap / spec dictionary and a normalization map** (the `serialization-map.json` idea is worth copying), and as a free, ToS-safer (pre-scraped, MIT-ish) seed for *spec metadata*. Useless for live prices.

### Other repos found (for completeness)
- **JonathanVusich/pcpartpicker** (PyPI `pcpartpicker`): `API` class, `retrieve("cpu")` / `retrieve_all()`, async. Category-level bulk retrieval. https://github.com/JonathanVusich/pcpartpicker
- **pypartpicker2** (PyPI): `Scraper` class with `part_search()` / `fetch_product()`. Fork/alt API surface.
- **matyascimbulka/pcpartpicker** (Apify Actor, published 2025-01): hosted Playwright scraper that returns exactly the merchant price structure we want — `prices.lowestPrice` + `prices[]` with `merchant`, `availability`, `price`, `currency`, `buyLink`, plus `ratings`, `specification`, `reviews`. This is the cleanest *output schema* reference. Hosted/paid. https://github.com/matyascimbulka/pcpartpicker · https://apify.com/matyascimbulka/pcpartpicker-scraper/api
- **FocusedLoop/PC-Part-Picker-Scrapper-Bot** (Python, Selenium + NordVPN rotation): **explicitly abandoned — author says Cloudflare detected and blocked its bypass; will not fix.** A cautionary tale that VPN-IP rotation alone is dead.
- Older/dead: Jeet-Chugh/pcpartscraper (BS4, 2020), bryanyli/PCPPScraper (2019), bradynichols/pcpartpickerbot (Selenium, 2019), nynhex/soeltjen/luigi311 forks. All requests+BS4 era, predate current Cloudflare; **selector reference only.**

---

## 2. PCPartPicker structure & anti-bot

### Stack & what's exposed
- PCPartPicker is a **Django (Python) backend, jQuery/server-rendered frontend** (per staff comments), some Rust for perf. No SPA/JSON-first frontend. Source: https://pcpartpicker.com/forums/topic/389996-whats-pcpp-built-on
- **Product pages:** `https://pcpartpicker.com/product/<id>` (e.g. `/product/fN88TW`). Server-rendered HTML containing: title, specs table, rating, reviews, a **merchant price list** (per-vendor `base / promo / shipping / tax / total`, availability, buy link), and a **price history** chart.
- **Category/browse pages:** `https://pcpartpicker.com/products/<category>/` (cpu, video-card, memory, internal-hard-drive, etc.) — paginated lists (~30/page) with name, url, price, key specs. Filterable by spec.
- **Part lists / builds:** `/list/<id>` and `/list/<id>/by_merchant/` (the "Prices By Merchant" view groups a build's items per retailer). Source: https://pcpartpicker.com/list/LpZdbX/by_merchant/
- **Price history:** rendered as a chart on the product page; selectable range (120 days / 1 year). Availability and merchant coverage are **region-specific** (a part may have rich US history but sparse AU/UK), so region matters.
- **Regional domains/paths:** per-region subpaths/sites (`/`, `de.`, `es.`, `uk.`, `au.` etc.). `region` param in the wrappers selects this. Prices/merchants differ per region — for our USD enterprise tracker, pin to **US**.

### Internal JSON endpoint?
- There **is** an internal API, but PCPartPicker staff have repeatedly and explicitly stated it will **not** be made public ("There are no plans to create a public API for any part of the site."). Sources: https://pcpartpicker.com/forums/topic/360367-make-the-pcpartpicker-internal-api-public · https://pcpartpicker.com/forums/topic/421260-api
- No cleanly documented public XHR/JSON endpoint surfaced in research. Everything community-built **scrapes server-rendered HTML** (sometimes after JS render). There are undocumented internal XHR calls (filtering/pagination) you could discover via DevTools, but using them is both fragile and squarely against ToS. **Plan on HTML parsing, not a JSON API.**
- Third-party "API" products exist by *re-scraping* (Apify Actor above; Parse.bot's "PCPartPicker API" exposing `search_parts`, `get_part_details` with `specs`/`prices[]`/`buy_link`/`compatibility_links`, `get_<category>` paginated). These prove the data is extractable but are paid middlemen. https://parse.bot/marketplace/.../pcpartpicker-com-api

### How aggressive is the anti-bot?
- **Cloudflare, and it bites.** Plain datacenter/VPS requests get 403/429; TLS fingerprinting defeats naive header spoofing; JS challenges and Turnstile escalate against headless browsers. Per 2026 guidance: undetected-chromedriver / puppeteer-stealth / FlareSolverr's UC backend are now "easily detected"; the durable approaches are TLS-impersonation (`curl_cffi`/curl-impersonate) for light protection, or maintained stealth browsers (Nodriver, SeleniumBase UC Mode, Camoufox) + trusted (residential/mobile) IPs for hard challenges. Sources: https://scrapfly.io/blog/posts/how-to-bypass-cloudflare-anti-scraping · https://blog.apify.com/bypass-cloudflare/
- Practically: **low volume + a residential-looking IP + good TLS fingerprint usually passes.** It's *rate* and *IP reputation* that get you blocked, not a single well-formed request. This is good news for a benchmark source where we only need ~10-12 product pages refreshed daily.

---

## 3. Anti-bot / cost strategy (cheapest-first)

Our actual need is tiny: ~10-12 product pages, refreshed daily-to-weekly = **~70-350 requests/week**. That changes the economics completely — we do not need an enterprise unblocker.

Ranked cheapest → most expensive:

**(a) Polite rate-limited direct requests + TLS impersonation — RECOMMENDED START. ~$0.**
- Use **`curl_cffi`** (`impersonate="chrome"`) rather than plain `requests`/`requests-html` — it matches a real Chrome TLS/HTTP2 fingerprint, which is the single biggest reason naive scrapers 403. https://scrapfly.io/blog/posts/how-to-bypass-cloudflare-anti-scraping
- Rotate a small pool of realistic, current User-Agents; persist Cloudflare clearance cookies between requests; randomized 5-30s delays; 1 request at a time, no concurrency; nightly cron, not real-time.
- Cache hard (we only need a daily price). Honor `Retry-After`/back off on 429.
- At our volume this very likely just works from a clean residential IP. Wrap with `pypartpicker`'s `response_retriever` hook so the library parsing is reused but transport is ours.

**(b) Self-hosted egress rotation via Sean's homelab — CHEAP fallback. ~$0 marginal.**
- Sean has **Tailscale + homelab + a "nerd server" at 104.223.27.177.** Route the scraper's egress through a **residential home IP** (homelab behind a consumer ISP) via Tailscale exit-node, rather than the datacenter IP of `104.223.27.177` (datacenter IPs are pre-flagged by Cloudflare). A residential exit node is the cheap equivalent of a residential proxy for this tiny volume.
- Optionally self-host **FlareSolverr** (Docker, `ghcr.io/flaresolverr/flaresolverr`) to mint Cloudflare clearance cookies once per session, then replay with `curl_cffi` — but note FlareSolverr's UC backend is increasingly detected and **cannot solve Turnstile/CAPTCHA**. https://scrapeops.io/python-web-scraping-playbook/python-flaresolverr
- Caveat from the dead FocusedLoop repo: a *single* VPN/exit IP hammered too hard still gets blocked. Keep volume low and rotate among a couple of exit nodes if available.

**(c) Headless stealth browser (Playwright/Nodriver/Camoufox) — escalate only if (a)/(b) 403. ~$0 compute (we already run Playwright via MCP).**
- Use **Nodriver, SeleniumBase UC Mode, or Camoufox** (maintained) — NOT vanilla Playwright/Puppeteer or undetected-chromedriver (detected). Run headful-ish on the homelab, extract clearance cookies, hand off to the cheap HTTP path. Heavy (RAM/CPU) so reserve for cookie-minting, not every fetch.

**(d) Paid scraping APIs — LAST RESORT only.** Rough costs (per 1k successful requests):
- **Zyte:** $0.13-$1.27 HTTP / $1.01-$16.08 browser — cheapest for easy targets, unpredictable for Cloudflare. https://brightdata.com/blog/web-data/best-web-scraping-apis
- **Bright Data Web Scraper/Unlocker:** ~$0.75/1k, pay-per-success, highest success on protected sites. https://brightdata.com/pricing/web-scraper
- **ScraperAPI:** subscription, $29/mo for 100k credits (credits multiply 5-75x with JS render/premium proxy). https://www.scraperapi.com/web-scraping/python/libraries
- **ScrapingBee / ZenRows** (what N-O-U-R used): similar JS-render credit model.
- At ~350 req/wk these are all comfortably inside free tiers / a few dollars a month — but they're a recurring dependency and another vendor. Only adopt if Cloudflare hardens against (a)-(c).
- Raw residential proxy bandwidth (if we want our own rotation without a full API): Evomi ~$0.49/GB, DataImpulse/PacketStream/IPRoyal ~$1-1.75/GB, Decodo. Overkill for our volume. https://www.zenrows.com/blog/cheap-residential-proxies

**Recommendation:** start at **(a) `curl_cffi` + polite limits + cache**, egress through a **(b) homelab residential Tailscale exit node**, keep **(c)** as an on-demand cookie-minter, and only wire in **(d)** behind a feature flag if we get consistently blocked. Net cost target: **$0/mo.**

---

## 4. Fit for THIS project (be honest)

This tracker's catalog is **used enterprise gear**. PCPartPicker is a **new/consumer/prosumer retail aggregator**. The overlap is partial and asymmetric.

### Where PCPartPicker genuinely helps (≈10-12 of 34 catalog items)
- **Workstation GPUs** — RTX 6000 Ada, RTX PRO 6000/4000 Blackwell, possibly L4/T4 (these straddle workstation/datacenter; coverage thinner for pure datacenter SKUs). PCPP tracks workstation/consumer GPU retail prices well → great for a **"vs retail" benchmark**.
- **Consumer/prosumer NVMe & SSD** — anything in the catalog that's a retail M.2/2.5" SSD has solid PCPP coverage and price history.
- **DDR memory (non-ECC / UDIMM)** — consumer DDR4/DDR5 kits are well covered. Useful as a loose floor reference.
- **Threadripper / high-end consumer CPUs** — covered if any are in catalog.

### Where PCPartPicker is useless (the bulk of this catalog)
- **EPYC server CPUs** (7F72, etc.) — not a retail-channel part; PCPP has no/poor coverage.
- **RDIMM / LRDIMM ECC server memory** (Samsung M393…, etc.) — PCPP's memory category is consumer DIMMs; ECC RDIMM coverage is essentially absent.
- **Enterprise HDD** (nearline/SAS) and **server boards** (Supermicro H12SSL, ASRock Rack ROMED8-2T) — not retail consumer parts; no meaningful PCPP data.
- Even where PCPP has a SKU, its prices are **new-retail**, while our deals are **used/China-direct** — different price universe (often 2-4x our `target_price`).

### Benchmark source vs deal-listing source — recommendation
**Use PCPartPicker as a price-BENCHMARK / reference source, not a deal-listing source.**
- It is *not* a place to find used enterprise deals (no used market, no enterprise SKUs, ToS-hostile to high-frequency polling). Do **not** route it through the deal-scoring/notification pipeline as a listing feed.
- It *is* a good source to improve, for the ~10-12 consumer-adjacent items:
  - **`benchmark_median`** — sanity-check/refresh our hand-curated median against PCPP's current cheapest/median retail.
  - **A new "vs retail" delta** — "this used RTX 6000 Ada at $4,500 is X% below the $5,200 PCPP retail floor." This is a genuinely useful scoring/UI signal we don't have today.
  - Optionally a **`scam_floor` cross-check** for GPUs (if used asking price << some fraction of PCPP retail, flag).
- Refresh cadence: **daily at most, weekly is fine.** These are reference numbers, not live deals.
- Keep it **clearly labeled as a secondary/optional enrichment** that can be disabled without affecting the core eBay pipeline.

---

## 5. Adapter design

### Shared `SourceAdapter` interface
Introduce a source abstraction so eBay and PCPartPicker (and future sources) share one shape. PCPartPicker returns **benchmark/reference rows**, eBay returns **listings**; same normalized record, different `source` and usage downstream.

Normalized record (per the requested fields):

| field | type | PCPartPicker mapping |
|---|---|---|
| `source` | str | `"pcpartpicker"` |
| `source_listing_id` | str | PCPP product id from `/product/<id>` (e.g. `fN88TW`); for a specific merchant row, `"<id>:<merchant>"` |
| `title` | str | `Part.name` |
| `url` | str | canonical `https://pcpartpicker.com/product/<id>` |
| `price` | Decimal | per-merchant `total` (or `Part.cheapest_price.total` for the benchmark row) |
| `currency` | str | `Price.currency` (pin region=US → USD) |
| `shipping` | Decimal\|null | `Price.shipping` |
| `condition` | enum | always `"new"` (PCPP is retail) — important for scoring: never compare as a used listing |
| `availability` | str | merchant availability ("In stock"/"Out of stock") |
| `seller`/`merchant` | str | `Vendor.name` / merchant ("newegg", "bestbuy", …) |
| `catalog_item_id` | int\|null | resolved via catalog match (see below); null if unmatched |
| `raw_payload` | json | full parsed `Part`/vendor dict for audit/debug |
| `fetched_at` | datetime | UTC fetch timestamp |

Suggested interface (mirrors how the existing `ebay/` service is structured — `client.py` + `parser.py` + `rate_budget.py`):

```python
# app/services/sources/base.py
class SourceAdapter(Protocol):
    source: str
    async def fetch_for_catalog_item(self, item: CatalogItem) -> list[NormalizedListing]: ...

# app/services/sources/pcpartpicker/adapter.py
class PcPartPickerAdapter:
    source = "pcpartpicker"
    # transport: curl_cffi session (impersonate=chrome) injected as
    # pypartpicker Client(response_retriever=...), region pinned to US.
    # parse with pypartpicker, normalize to NormalizedListing.
```

### Catalog matching (the hard part)
- Add an **optional `pcpp_product_id` (or `pcpp_search_query`) field to `CatalogItem`** for the ~10-12 items that map to PCPP, resolved **once, manually** (no live search guessing — avoids noise and extra requests). For unmapped items the adapter simply does nothing.
- Do not auto-search by `keywords` (our keywords are eBay-tuned, e.g. "China direct"; they won't match PCPP's retail catalog cleanly).

### Rate-limit / budget notes
- **Separate per-source budget — NOT eBay's 5000/day bucket.** Add a `pcpartpicker` bucket to the rate-budget layer with a tiny ceiling, e.g. **≤200 requests/day, ≥5s min spacing, 1 concurrent**. PCPP volume must never affect eBay's tiered poller accounting.
- Schedule on the **slow tier only** (daily/weekly), separate from P0-P3 eBay tiers.
- On `CloudflareException`/`RateLimitException`/403/429: exponential backoff, then **circuit-break and disable the source for the day** (don't retry-storm into a harder block). Log and surface as "PCPP benchmark stale" rather than failing the run.
- Feature-flag it: `ENABLE_PCPARTPICKER=false` by default (mirrors the `USE_MOCK_EBAY` convention). Ship a mock/fixture adapter for tests.

### ToS / legal caveats (read before shipping)
- **PCPartPicker's ToS explicitly prohibits this.** The license is "personal and non-commercial" and expressly forbids: collection/use of product listings, descriptions, or prices; benchmark/product/user data; derivative use; and "use of data mining, robots, or similar data gathering and extraction tools." Sources: https://pcpartpicker.com/forums/topic/315918-is-scraping-against-tos (community reading of the ToS) and the ToS prohibited-use list.
- `robots.txt` is not itself legally binding, but **ToS can create contractual liability**, and ignoring robots/ToS is used as evidence of knowing violation in scraping disputes. Sources: https://bytetunnels.com/posts/is-robots-txt-legally-binding-scraping-law-explained/ · https://www.scrapingbee.com/blog/is-web-scraping-legal/
- **Mitigations / posture for a personal homelab tool:**
  - Keep volume *minimal* (a dozen product pages, daily) — this is the difference between "respectful personal use" and "data mining."
  - **Cache aggressively**; never republish or resell PCPP data; use it only as a private internal benchmark.
  - Make it **off by default and trivially disableable.**
  - Prefer the **static `docyx/pc-part-dataset`** (already-scraped, redistributable) for spec/bootstrap data where possible, reducing live hits.
  - The "correct" path per PCPP staff is to **contact the owner** for permission/data licensing; realistically unlikely to be granted, so the above keeps risk proportionate to a non-commercial personal project.

### Recommended build order
1. Add `SourceAdapter`/`NormalizedListing` abstraction + a `pcpartpicker` rate bucket (no eBay impact).
2. Add optional `pcpp_product_id` to the ~10-12 mappable `CatalogItem`s.
3. Implement `PcPartPickerAdapter` using `pypartpicker` for parsing + `curl_cffi` (`impersonate=chrome`) transport via `response_retriever`, region=US, behind `ENABLE_PCPARTPICKER`.
4. Egress through homelab residential Tailscale exit node; FlareSolverr/Camoufox cookie-mint only if blocked.
5. Store benchmark rows; compute/refresh `benchmark_median` + new "vs retail" delta for those items; surface in UI as a reference, not a deal.
6. Paid API fallback (Zyte/Bright Data) only if Cloudflare consistently blocks the free path.

---

## Key sources
- pypartpicker: https://github.com/lucwl/pypartpicker · https://pypi.org/project/pypartpicker/ (v2.0.5, 2024-12-28)
- N-O-U-R/PcPartPicker-Scraping (Node + ZenRows): https://github.com/N-O-U-R/PcPartPicker-Scraping
- docyx/pc-part-dataset (static, last refresh 2024-05-14): https://github.com/docyx/pc-part-dataset
- Apify PCPP Actor output schema: https://apify.com/matyascimbulka/pcpartpicker-scraper/api
- PCPP no public API (staff): https://pcpartpicker.com/forums/topic/360367-make-the-pcpartpicker-internal-api-public · https://pcpartpicker.com/forums/topic/421260-api
- PCPP stack (Django): https://pcpartpicker.com/forums/topic/389996-whats-pcpp-built-on
- PCPP merchant-price-list view: https://pcpartpicker.com/list/LpZdbX/by_merchant/
- Cloudflare bypass 2026: https://scrapfly.io/blog/posts/how-to-bypass-cloudflare-anti-scraping · https://blog.apify.com/bypass-cloudflare/
- FlareSolverr: https://scrapeops.io/python-web-scraping-playbook/python-flaresolverr
- Scraping API / proxy pricing: https://brightdata.com/blog/web-data/best-web-scraping-apis · https://brightdata.com/pricing/web-scraper · https://www.zenrows.com/blog/cheap-residential-proxies
- ToS / legality: https://pcpartpicker.com/forums/topic/315918-is-scraping-against-tos · https://bytetunnels.com/posts/is-robots-txt-legally-binding-scraping-law-explained/ · https://www.scrapingbee.com/blog/is-web-scraping-legal/
