# MVP2 Source Research — US Used/Refurb Enterprise & Workstation Hardware

> Goal: expand the deal tracker beyond eBay. This report vets US-based sources for
> buying used/refurbished EPYC CPUs, workstation/DC GPUs, ECC RDIMM/LRDIMM, NVMe/enterprise
> SSDs, enterprise HDDs, server motherboards, ConnectX NICs, and chassis, and rates each
> for programmatic price polling.
>
> Date: 2026-06-02. Findings are from live web research; verify robots.txt/ToS before building.

---

## TL;DR

- **Most independent used-server retailers run on Shopify or standard ecommerce stacks.** That is the single most important finding: Shopify stores expose a public, undocumented-but-stable `/products.json` endpoint and embed schema.org `Product`/`Offer` JSON-LD on every product page. This makes them *Easy* to poll structurally, even though none publish a formal "buyer API."
- **Newegg has a real API, but it is a seller/Marketplace API** (manage your own listings, inventory, price) — not a buyer-facing price-query API. Not useful for polling third-party prices.
- **Amazon Product Advertising API (PA-API 5.0)** is the only sanctioned way to read Amazon prices, but it is gated behind Amazon Associates approval **and** an ongoing **10 qualified sales / trailing 30 days** requirement, plus a hard rule against caching/displaying static prices. High friction.
- **Micro Center has no public API**, is JavaScript-rendered, and pricing/stock are per-store (store-ID gated). Scrape-only and anti-bot defended.
- **LabGopher is effectively dead** (site up but no longer pulling eBay). **RackRat** (rackrat.net) is the live successor eBay aggregator — but it is a competitor doing exactly what this project does, not a data source to consume.
- **Recommended first adapters: TechMikeNY, UnixSurplus, ServerMonkey (all Shopify-class), plus Amazon Renewed via PA-API if the Associates gate can be cleared.** See Section 4.

---

## 1. Online used-server-parts retailers (USA)

Feasibility is for *programmatic price polling* of their public catalog. "Shopify-class" means the store
exposes the standard Shopify `/products.json` JSON endpoint and/or schema.org JSON-LD product markup,
which is the easiest possible scrape target (structured, paginated, stable).

| # | Name | URL | Specializes in | API / structured data / ToS posture | Feasibility |
|---|------|-----|----------------|--------------------------------------|-------------|
| 1 | **TechMikeNY** | https://techmikeny.com | Configure-to-order used Dell/HPE rack servers, EPYC & Xeon, RAM/CPU/drive upgrades; strong homelab rep | Shopify-class storefront → likely `/products.json` + JSON-LD `Product/Offer`. No formal API. Public catalog, scrape-tolerant by convention. Also sells via eBay (`techmikeny` store, 99.8%) so some inventory is already in the eBay feed. | **Easy** |
| 2 | **UNIXSurplus** | https://unixsurplus.com | Silicon Valley wholesaler; Supermicro/Dell/Gigabyte/Quanta, EPYC CTO barebones, NVMe, NICs, HDDs, networking | Standard ecommerce catalog with full category tree (`/all-servers`, Components, Hard Drives, Networking). Public pricing. Check for Shopify/Magento `/products.json` or sitemap. | **Easy–Medium** |
| 3 | **ServerMonkey** | https://www.servermonkey.com | Used/refurb Dell/HPE/Supermicro/Cisco; deep parts & upgrades tree (Processors, Memory, Drives, NICs, RAID, Optics, **Accelerators**: H100/L40S/A10/MI300x) | Has an online quoting tool and a structured category catalog; warranty terms public. Best-organized GPU/accelerator taxonomy of the bunch. Likely scrapeable JSON-LD. | **Medium** |
| 4 | **The Server Store** | https://www.theserverstore.com | Refurb Dell/HP/Supermicro/Cisco, configure-to-order rack/tower/blade/GPU servers | Standard storefront, public pricing, configurable products. | **Medium** |
| 5 | **SaveMyServer** | https://savemyserver.com | New/refurb servers + parts (Xeon, **EPYC**, RAM 8GB–2TB, SSD/NVMe/HDD, RAID); "Server Design Lab" configurator | Shopify-class (`savemyserver.com` storefront). Notably **updates pricing weekly** and flags DDR4 shortage volatility — quotes valid 4 days. Good for memory price signals. | **Easy–Medium** |
| 6 | **PCSP — PC Server & Parts** | https://pcserverandparts.com | Refurb Dell/HPE/Lenovo servers + workstations, GPUs, enterprise networking; New Hudson, MI | Standard storefront, public catalog, multi-brand parts. | **Medium** |
| 7 | **Newegg (refurb/marketplace)** | https://www.newegg.com (API: https://developer.newegg.com) | Huge marketplace incl. refurb server parts, EPYC, GPUs, ECC RAM, NVMe | **Newegg Marketplace API exists but is seller-side** (manage *your* items/inventory/price via API key+secret). No buyer price-query API. Buyer-side = scrape (anti-bot defended) or affiliate feed. | **Hard** (API not buyer-facing) |
| 8 | **Amazon Renewed** | https://www.amazon.com (API: PA-API 5.0, https://webservices.amazon.com/paapi5) | Renewed/refurb server parts, RAM, SSDs, some EPYC/GPU; huge but variable | **PA-API 5.0** is the sanctioned read API. Requires Amazon Associates approval, **3 sales/180d to onboard + 10 qualified sales/trailing 30d to keep access**, ~1 req/s & ~8,640 req/day base limits, and **forbids caching/static price display**. Powerful but high-friction & policy-bound. | **Medium** (with Associates account) / **Hard** (without) |
| 9 | **Provantage** | https://www.provantage.com | Large IT/electronics reseller, mostly new but deep enterprise SKU coverage incl. memory, NICs, drives | Older-style catalog, public pricing, SKU-stable URLs. No public API found; scrape feasible. Mostly *new*, so less "deal" overlap. | **Medium** |
| 10 | **Bargain Hardware** | https://www.bargainhardware.co.uk | Refurb servers + components (CPU/RAM/GPU/NVMe/RAID/PSU), configure-to-order | **UK-based** (ships worldwide; USD pricing available). Magento-class store, schema.org markup. Good *components* catalog but shipping/VAT/currency complicate US price comparison. | **Medium** (non-US logistics) |
| 11 | **Natex / Tech-America** | https://natex.us | Liquidation-priced Supermicro barebones, CPUs, RAM, NICs; popular with homelab for cheap bulk DDR4/NICs | Lightweight storefront, public pricing, low SKU count but high deal density. No API; simple scrape. | **Easy–Medium** |
| 12 | **Delta Computer Group** | https://www.deltacomputergroup.com | Refurb Dell/HPE/IBM/Sun servers, storage, parts | RFQ-heavy / quote-driven model; not all pricing is public. Weaker for automated polling. | **Hard** (quote-gated pricing) |
| 13 | **Cloud Ninjas** | https://cloudninjas.com | New/refurb servers + spare parts, warranty programs | Shopify-class storefront (`/collections/...`), public pricing → likely `/products.json`. | **Easy–Medium** |
| 14 | **Dedicated Networks Inc.** | https://dedicatednetworksinc.com | Large used/refurb networking + server inventory (5000+ SKUs), condition grading (F/S, NOB, used/refurb) | Public catalog with condition grades; networking/NIC heavy. No API found; scrape feasible. | **Medium** |
| 15 | **Vibrant Technologies** | https://store.vibrant.com | Used HP/IBM/Sun servers, CPUs (incl. EPYC), memory, disk; RFQ-oriented | Cart exists but much is RFQ/quote-driven. Public pricing partial. | **Hard** (quote-gated) |

Other reputable names surfaced (lower priority): **ServerSource** (UK), **NewServerLife / ServerMall / ServerBasket** (refurb full-system specialists, often non-US or RFQ), **Orange Computers** (eBay-first, DL360 G8 era), **King of Servers** (UK), **LASYSCO** (enterprise SSD wholesale), **Dell Outlet / HP Renew** (OEM-refurb factory outlets — official, warrantied, polite robots, but mostly current-gen pricing).

> **Practical scrape note:** for any Shopify-class store, `https://<domain>/products.json?limit=250&page=N`
> returns structured JSON (title, variants, price, sku, available, images) without rendering. This is the
> single highest-leverage technique for ~half this list. Always check `robots.txt` and rate-limit politely
> (1 req / few seconds); these are small businesses, not hyperscalers.

---

## 2. Brick-and-mortar with online inventory/pricing

### Micro Center (the main one)
- **No official public API.** Repeatedly requested in Micro Center's own community forums; never confirmed/shipped (https://community.microcenter.com/discussion/16617/micro-center-api).
- Site is **consumer-browse oriented, JavaScript-rendered**, and **pricing + stock are per-store**, selected via a **store-ID parameter** (e.g. 25 locations). To get accurate data you must poll *per-store SKU pages* with the store context set.
- **Rate limiting / IP blocking** kick in on aggressive scraping.
- Existing community tooling proves it's doable: open-source `microcenter-stock-checker` and `StockSmart` (GitHub) check per-SKU stock; commercial actors (Apify "Micro Center Electronics Scraper", Real Data API, Retail Scrape) sell managed scraping across all stores with proxy rotation.
- **Feasibility: Hard / scrape-only / ToS-risky.** Only worth it for a few high-value SKUs (e.g., specific NVMe or GPU SKUs) at a single relevant store, not broad catalog polling. Micro Center's relevance to *used/refurb enterprise* gear is also low — it's mostly new consumer/prosumer parts (consumer NVMe, GPUs, some ECC). Marginal fit for the EPYC/ConnectX/enterprise focus.

### Other B&M chains
- **Fry's Electronics is defunct** (closed 2021) — no successor with comparable inventory.
- **Best Buy** has an official Products API (free dev key) but negligible enterprise/refurb-server overlap.
- **Newegg** runs hybrid online + a few physical stores but is effectively online-only for this purpose (see Section 1).
- No other national B&M chain meaningfully stocks used enterprise server hardware. B&M is **not a priority** for this tracker; Micro Center is the only candidate and is a marginal, scrape-only one.

---

## 3. Aggregators / community signals

| Source | URL | What it is | Feasibility for us |
|--------|-----|------------|--------------------|
| **LabGopher** | https://labgopher.com | Historic eBay rackmount-server deal scorer (~30 models, ML-scored). **Now defunct** — site up but no longer pulling eBay results. | **Dead.** Do not depend on it. |
| **RackRat** | https://rackrat.net (scoring: /how-scoring-works.html) | Live LabGopher successor. Scans tens of thousands of eBay rackmount listings daily, scores 0–100 on value, filters by form factor/CPU family/RAM/bays/PSU/region. Affiliate-monetized. | **Competitor, not a feed.** It consumes the *same* eBay source this project already polls. No public API. Useful as a **benchmark for our own scoring algorithm**, not as a data source. |
| **r/homelabsales** | reddit.com/r/homelabsales | Peer-to-peer homelab marketplace subreddit; frequent EPYC/RAM/NIC/SSD deals from individuals | Reddit has an official API (OAuth, rate-limited, free tier exists). Listings are **free-text, unstructured** (no consistent price/condition fields) → heavy NLP/parsing needed, and many are sold/traded fast. **Medium-Hard**; high signal-to-noise cost. Good *future* source for genuine below-market deals. |
| **ServeTheHome (STH) Forums** | https://forums.servethehome.com | "Great Deals" + Marketplace/"system pull" sections; expert community | XenForo forum; no API. Scrape-only, unstructured threads, low volume. **Hard / low ROI** for structured polling; better as a manual deal-signal source. |
| **Price-comparison feeds** | — | No general-purpose feed aggregates *used enterprise* parts across these niche retailers. PCPartPicker etc. track *new* consumer parts only. | No usable aggregator feed exists for this niche. |

---

## 4. Recommended integration priority (MVP2)

Build adapters in this order. All ranked on data quality, polling feasibility, and overlap with the
catalog's EPYC / workstation-GPU / ECC / NVMe / NIC focus.

1. **TechMikeNY** — *Build first.* Shopify-class (`/products.json` likely available → clean structured JSON, no JS rendering), strong EPYC/Dell/HPE configure-to-order inventory, excellent homelab reputation = trustworthy prices, and it already overlaps the existing eBay feed (the `techmikeny` eBay store) so it's a low-risk validation target. API-friendly-by-convention; polite polling, not ToS-hostile.
2. **UNIXSurplus** — *Build second.* Broad and deep: EPYC CTO barebones, Supermicro/Quanta, plus dedicated **Components / Hard Drives / Networking (NICs)** categories — best single-source coverage of the *parts* side (NVMe, NICs, HDDs) the catalog cares about. Structured catalog; verify `/products.json` or sitemap. Low ToS risk.
3. **ServerMonkey** — *Build third.* Best taxonomy for **GPUs/accelerators** (explicit H100/L40S/A10/L4/MI300x tree) and a clean Processors/Memory/Drives/NICs parts tree. Online quoting tool implies structured backend data; JSON-LD scrape feasible. Fills the workstation/DC-GPU gap the first two don't fully cover.
4. **Amazon Renewed via PA-API 5.0** — *Build only if the Associates gate is clearable.* Highest data quality and a real sanctioned API with clean fields, but blocked behind Associates approval + **10 qualified sales / 30 days** to retain access, ~1 req/s budget, and a **no-static-price-caching policy** (must refresh, can't store stale prices for display). Treat as a stretch goal; do not block MVP2 on it.

**Honorable mentions for later:** SaveMyServer (weekly-refreshed pricing → good *memory* price signal during the DDR4 shortage), Natex (high deal-density on cheap DDR4/NICs/barebones), Cloud Ninjas (Shopify-class, easy).

**Flagging by ToS/API posture:**
- *Scrape-only but low-risk (small-biz storefronts, polite-poll fine):* TechMikeNY, UnixSurplus, ServerMonkey, SaveMyServer, PCSP, Natex, Cloud Ninjas, Dedicated Networks.
- *Sanctioned API but policy-heavy:* Amazon (PA-API — caching ban, sales quota), Newegg (seller-only API, no buyer query path).
- *Scrape-only AND ToS-risky / anti-bot:* Micro Center (per-store JS, IP blocking), Newegg buyer-side.
- *Quote-gated (pricing not reliably public):* Delta Computer Group, Vibrant, some Provantage SKUs.
- *Non-US logistics:* Bargain Hardware, ServerSource, King of Servers (UK).

> Recommendation: ship MVP2 with **eBay (existing) + 2–3 Shopify-class adapters (TechMikeNY, UnixSurplus, ServerMonkey)**. They give the best coverage/effort ratio and stay clear of ToS minefields. Defer Amazon and Micro Center.

---

## 5. Adapter design notes

### Shared listing schema (every source maps to this)
To plug into one poller/scoring abstraction, each adapter must normalize to a common record:

| Field | Type | Notes |
|-------|------|-------|
| `source` | enum/string | `ebay`, `techmikeny`, `unixsurplus`, `servermonkey`, `amazon`, ... |
| `source_listing_id` | string | Stable per-source ID (Shopify variant ID, ASIN, eBay item ID) — dedup key with `source`. |
| `title` | string | Raw listing title (feeds catalog-matching/NLP). |
| `url` | string | Canonical product/variant URL (include affiliate tag for Amazon). |
| `price` | decimal | Current price; **currency-normalize to USD**. |
| `currency` | string | ISO 4217; needed for UK sources (Bargain Hardware). |
| `shipping` | decimal/null | Often absent or "configure"; treat null explicitly — shipping swings deal score (cf. RackRat weighting region/shipping heavily). |
| `condition` | enum | Map vendor grades → canonical set (`new`, `refurb`, `used`, `for-parts`). Vendors differ: eBay grades, Amazon "Renewed", DNI's F/S/NOB/used. |
| `availability` | enum/bool | `in_stock` / `out_of_stock` / `configure-to-order` / `quote`. Shopify `available` bool maps directly. |
| `seller` | string/null | Marketplace sub-seller (eBay seller, Amazon merchant); null for first-party retailers. |
| `catalog_item_id` | FK/null | Result of matching `title`/specs to the 34-item curated catalog (reuse existing scoring matcher). |
| `raw_payload` | JSON | Store the unparsed source record (Shopify product JSON, PA-API item, scraped JSON-LD) for re-parsing/debug without re-fetching. |
| `fetched_at` | timestamp | Required for staleness; **mandatory for Amazon** (PA-API forbids displaying stale prices). |

This mirrors the existing eBay-derived shape, so the scoring engine (6-component algo, scam-floor check)
stays source-agnostic — adapters are thin "fetch → normalize → emit common record" units behind the existing
poller/`RateBudgetManager` abstraction.

### Per-source auth / rate-limit considerations
- **Shopify-class (TechMikeNY, UnixSurplus*, ServerMonkey*, SaveMyServer, Cloud Ninjas):** No auth. Fetch `/products.json?limit=250&page=N` (or parse JSON-LD if `/products.json` is disabled). Self-impose a polite delay (1 req / 2–5 s) and a per-host daily cap; set a descriptive `User-Agent`. No vendor rate limits published, so **we** own the budget — fold each host into a per-source bucket in `RateBudgetManager` (don't share eBay's 5,000/day budget; these are independent). *(Verify the exact platform per site — confirm Shopify vs Magento before assuming `/products.json`.)*
- **Amazon PA-API 5.0:** AWS SigV4 request signing with Access Key + Secret + Associate Tag. Hard limits ~1 TPS / ~8,640 req/day (scales with sales). Must maintain **10 qualified sales / 30 days** or access drops (`AssociateNotEligible`). **Cannot cache/display stale prices** — poll on-demand or with short TTL only. Implement 429 `TooManyRequests` backoff. Use `SearchItems`/`GetItems` with `Condition=Used`/`Refurbished` filters.
- **Newegg Marketplace API:** API Key + Secret headers, but **seller-scoped** — cannot query arbitrary third-party prices. Not usable for our polling. (Skip.)
- **Micro Center (if ever built):** No auth, but JS-rendered + per-store (`storeid`) + anti-bot. Would need a headless browser or a paid scraping actor (Apify) and per-store SKU targeting. High maintenance, ToS-risky — gate behind a feature flag and limit to a handful of high-value SKUs.
- **Reddit r/homelabsales / STH (future):** Reddit OAuth app (free tier, ~60–100 req/min); STH = scrape XenForo. Both need free-text NLP to extract price/condition; treat as a separate "community signal" pipeline, not a price-poll adapter.

### Robustness notes
- Scraped sources break when markup changes — wrap each adapter in defensive parsing + a health check (e.g., "got 0 items" alarm) and prefer `/products.json` / JSON-LD over CSS-selector scraping where possible.
- Respect `robots.txt` per host; these are small businesses — a hostile crawl could get the tracker IP-banned and is reputationally bad.
- Dedup across sources: the same physical eBay store (e.g., TechMikeNY) appears both in the eBay feed and its own site — dedup on `(source, source_listing_id)` and optionally cross-source on normalized title + price to avoid double-counting.

---

## Sources

- Used EPYC server buying guide / refurb vendor landscape — https://electronics.alibaba.com/buyingguides/used-amd-epyc-server-buying-guide
- TechMikeNY — https://techmikeny.com
- UNIXSurplus — https://unixsurplus.com , https://unixsurplus.com/all-servers
- ServerMonkey — https://www.servermonkey.com
- The Server Store — https://www.theserverstore.com
- SaveMyServer — https://savemyserver.com
- PCSP (PC Server & Parts) — https://pcserverandparts.com
- Bargain Hardware (UK) — https://www.bargainhardware.co.uk , /components
- Cloud Ninjas — https://cloudninjas.com/collections/cloud-ninjas-servers
- Dedicated Networks Inc. — https://dedicatednetworksinc.com
- Vibrant Technologies — https://store.vibrant.com/used-servers-for-sale.aspx
- Used-server reseller warranty comparison (Lawrence Systems) — https://forums.lawrencesystems.com/t/comparison-of-used-server-re-sellers-that-offer-extended-warranties/1662
- Newegg Marketplace API (seller-side) — https://developer.newegg.com , /newegg_marketplace_api/newegg_marketplace_api_authentication
- Amazon Product Advertising API 5.0 — https://webservices.amazon.com/paapi5/documentation
- Amazon PA-API eligibility / 10-sales rule / rate limits — https://www.keywordrush.com/blog/fix-amazon-paapi-too-many-requests , https://www.keywordrush.com/blog/amazon-pa-api-associatenoteligible-error-is-there-a-new-10-sales-rule , https://www.alliancevirtualoffices.com/virtual-office-blog/what-qualifies-you-to-be-an-amazon-affiliate
- Micro Center — no official API (community) — https://community.microcenter.com/discussion/16617/micro-center-api , https://community.microcenter.com/discussion/6232/microcenter-api
- Micro Center scraping options — https://apify.com/fortuitous_pirate/microcenter-scraper , https://www.realdataapi.com/scraping-micro-center-product-data-real-time-electronics-insights.php , https://github.com/legitosaurus/microcenter-stock-checker , https://github.com/ayoTyler/StockSmart
- LabGopher (defunct) — https://labgopher.com
- RackRat (LabGopher successor) — https://rackrat.net/ , https://rackrat.net/how-scoring-works.html
- LabGopher gone / RackRat alternative — https://www.virtualizationhowto.com/2026/01/labgopher-is-gone-and-rackrat-is-the-alternative-homelab-builders-are-turning-to/
- ServeTheHome forums — https://forums.servethehome.com/index.php
- Homelab sources discussion (Spiceworks, Level1Techs) — https://community.spiceworks.com/t/where-do-you-get-used-equipment-for-your-home-lab/936438 , https://forum.level1techs.com/t/retired-server-hardware/165900
- Shopify structured data / `/products.json` & JSON-LD basis — https://shopify.dev/docs/api/liquid/filters/structured_data , https://www.hulkapps.com/blogs/shopify-hub/structured-data-for-shopify-the-ultimate-guide
