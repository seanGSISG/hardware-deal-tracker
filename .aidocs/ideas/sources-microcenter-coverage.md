---
title: "Cover Micro Center pricing without spoofing a bot-block"
area: "sources"
status: idea
filed: 2026-08-26
revisit: "Sean picks a route (Slickdeals RSS vs residential-egress browser), or Micro Center publishes a feed/API"
origin_session: "[[2026-08-26-s1]]"
---

# Cover Micro Center pricing without spoofing a bot-block

## Origin
Filed while adding the Intel Arc Pro B70 watches (2026-08-26). Sean asked to "make
sure that we are monitoring microcenter". We are not, and the MVP3 NO-GO still
holds — but the *reason* was re-measured rather than inherited, so this records
the evidence and the two compliant routes instead of just repeating "deferred".

## Trigger to revisit
Pick this up when Sean decides which of the two routes below he wants, or if Micro
Center ever exposes an official feed/API. It is also worth revisiting if the B70
(or any future new-retail part) turns out to be a Micro-Center-exclusive, since
eBay-only coverage then misses the actual buying channel entirely.

## Measured state (2026-08-26, from the Spark host egress)

| Path | Result |
|------|--------|
| `GET /robots.txt` | Cloudflare managed challenge — their crawl policy is unreadable without solving it |
| `GET /search/search_results.aspx?Ntt=…` | 403 |
| `GET /sitemap.xml` | 403 |
| `GET /product/<id>/x.aspx` | 403 |
| `HEAD /` as `curl/8.5.0` | 403 |
| `HEAD /` as desktop-Chrome UA | 403 |
| `HEAD /` as a Googlebot UA | **200** |

That last row is the trap. Micro Center will answer a search-engine user-agent,
so a two-line UA change "works". That is user-agent spoofing to defeat an
explicit anti-bot control — **deliberately not implemented and not to be
implemented**, regardless of how convenient it is. Any future session that
rediscovers the 200 should stop here.

## Open questions
- Q1 — Does Sean want *posted deals* (Slickdeals) or *true store pricing* (browser)? They answer different questions.
- Q2 — If browser: which host owns the job — cachy or thepower — and does it run headless on a schedule, or only on demand?
- Q3 — Micro Center pricing is per-store. Which store ID(s) matter? (Nearest-store-only, or a set?)
- Q4 — Is in-store-only pricing even actionable for Sean, or does he only care about ship-to-home?
- Q5 — Slickdeals prices are user-submitted and unverified. Benchmark-only, like PCPartPicker, or is that too weak to bother?

## Proposed design (sketch)

**Route A — Slickdeals RSS (compliant, cheap, partial).**
- `slickdeals.net/newsearch.php?q=<terms>&searcharea=deals&searchin=first&rss=1`
  returns 200 with 25 items, no anti-bot. Verified 2026-08-26; carries Micro
  Center deals including their PowerSpec house brand.
- New `app/services/sources/slickdeals.py` adapter + its own `SourceRateBudget`
  bucket, same shape as the Shopify adapters.
- **Benchmark-only, never scored** — user-submitted prices, same posture as PCPartPicker.
- Catches deals someone bothered to post. Misses quiet price drops entirely.

**Route B — residential-egress browser (compliant, accurate, more work).**
- Reuse the posture already built for PCPartPicker (`docs/PCPARTPICKER_EGRESS.md`):
  flag-gated, circuit breaker, low cadence.
- Difference: fetch runs from a real browser on Sean's own residential connection
  (cachy / thepower) and his own session — not a datacenter IP pretending to be a crawler.
- Only route that sees true store-scoped pricing. Needs a store ID in config.

**Route C — do nothing automated.** Micro Center pricing is store-local and Sean
is in range of a store; a manual check may genuinely beat a fragile scraper.

## Blast radius
Route A: one new adapter + rate bucket + registry entry + `SOURCE_ROADMAP.md`.
Low risk — benchmark-only means it cannot create a false hot-deal alert.
Route B: adapter + egress gating + a scheduled job on a *different machine* than
the stack, which is a new operational surface (that host must be up for the
source to work). Worst case is a silent dead source, so it needs the same
"verify, don't trust the registry" treatment the Shopify sources needed in June.

## Notes / research
- Amazon PA-API is a separate deferred item with a different blocker (Associates
  affiliate-sales quota), tracked in `docs/SOURCE_ROADMAP.md`.
- The Shopify re-verification (2026-06-30) is the cautionary precedent: 3 of 6
  "live" sources had silently rotted. Whatever route is picked needs a re-probe
  cadence, not a one-time verification.
