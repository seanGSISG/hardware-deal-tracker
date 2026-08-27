---
title: "Cover Micro Center pricing without spoofing a bot-block"
area: "sources"
status: idea
filed: 2026-08-26
revisit: "Sean picks Slickdeals-RSS vs manual, or Micro Center publishes a feed/API"
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

### The egress theory was wrong (tested same day)

The first version of this file proposed a "residential-egress browser" route,
reusing the PCPartPicker posture. **That was wrong, and the correction matters
more than the original idea.** Every probe above already ran from Sean's own
residential WAN (`24.128.83.160` = `wan.lsdmt.me`) — not a datacenter IP — and
was refused anyway. Two more clients on that same IP:

| Client | Result |
|--------|--------|
| Playwright/Chromium (automation-flagged) | stuck on `Just a moment...`, 403, never resolves |
| Sean's real desktop Chrome, via the extension | stuck on "Performing security verification", never resolves |

Micro Center's challenge keys on the **client**, not the network. PCPartPicker's
blocker was IP reputation; this one is automation fingerprinting, so the posture
does not transfer. Getting an automated client past it means defeating a
bot-verification interstitial — prohibited, full stop, no matter which machine
it runs on. **Route B is dead.** Do not resurrect it on the theory that a
different host or a different browser would help; both were tried.

## Open questions
- Q1 — Is a Slickdeals-derived signal (posted deals only, user-submitted prices) worth an adapter at all, or is the honest answer "check it yourself"?
- Q2 — If Slickdeals: query per catalog item, or one broad query filtered locally? Per-item is cleaner but burns the rate bucket faster.
- Q3 — Is in-store-only pricing even actionable for Sean, or does he only care about ship-to-home? If ship-to-home only, Micro Center matters much less than this file assumes.
- ~~Q4 — which host runs the browser job~~ — moot, Route B is dead.
- ~~Q5 — which store ID~~ — moot for the same reason.

## Proposed design (sketch)

**Route A — Slickdeals RSS (compliant, cheap, partial).**
- `slickdeals.net/newsearch.php?q=<terms>&searcharea=deals&searchin=first&rss=1`
  returns 200 with 25 items, no anti-bot. Verified 2026-08-26; carries Micro
  Center deals including their PowerSpec house brand.
- New `app/services/sources/slickdeals.py` adapter + its own `SourceRateBudget`
  bucket, same shape as the Shopify adapters.
- **Benchmark-only, never scored** — user-submitted prices, same posture as PCPartPicker.
- Catches deals someone bothered to post. Misses quiet price drops entirely.

**~~Route B — residential-egress browser~~ — RULED OUT, see above.** Tried from
the residential IP with both an automation-driven Chromium and Sean's own Chrome;
both stall on the challenge. Kept in this file only so nobody re-proposes it.

**Route C — do nothing automated.** Micro Center pricing is store-local and Sean
is in range of a store; a manual check may genuinely beat a fragile scraper. With
Route B dead this is now a serious contender, not a fallback — pair it with a
`REMINDERS.md` row if it should recur.

## Blast radius
Route A: one new adapter + rate bucket + registry entry + `SOURCE_ROADMAP.md`.
Low risk — benchmark-only means it cannot create a false hot-deal alert.
Route B: n/a, ruled out.

## Notes / research
- Amazon PA-API is a separate deferred item with a different blocker (Associates
  affiliate-sales quota), tracked in `docs/SOURCE_ROADMAP.md`.
- The Shopify re-verification (2026-06-30) is the cautionary precedent: 3 of 6
  "live" sources had silently rotted. Whatever route is picked needs a re-probe
  cadence, not a one-time verification.
