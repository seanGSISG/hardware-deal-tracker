---
title: "Cover Micro Center pricing without spoofing a bot-block"
area: "sources"
status: idea
filed: 2026-08-26
revisit: "PriceLasso proves out (or does not), or Micro Center ships an official API"
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

## Route A (Slickdeals) is also dead — robots.txt, checked 2026-08-26

Recommended before checking `robots.txt`. That was the same mistake as Route B,
so recording the correction rather than quietly dropping it:

```
slickdeals.net/robots.txt
  line 100:  Disallow: /newsearch.php?*rss=*      <- the exact endpoint proposed
  line 115:  Disallow: /search*
  line  53:  Disallow: /deal-feed/*
  line 123:  Disallow: /syndicated/*
```

The searchable RSS feed *works* (200, and it does return Arc Pro B70 + Micro
Center results) but is explicitly disallowed to automated clients. This repo's
own posture is a per-source robots/ToS gate, so that endpoint is off limits.

The only permitted feed is the FeedBurner front page
(`feeds.feedburner.com/SlickdealsnetFP`, a different host, published for
syndication). Fetched and inspected: 25 items of general-consumer front-page
deals — contact cement, LEGO, nail clippers — **zero Micro Center items and zero
enterprise/GPU hardware**. Useless for this catalog even setting robots aside.

## Why no proxy fixes this (researched 2026-08-26)

Sean asked whether cheap residential proxies would get us in. They will not, and
the evidence is already in this file: **a Googlebot user-agent returned 200 from
the very same residential IP that `curl` and Chrome got 403/challenged on.** Same
IP, different outcome — so the discriminator is the client fingerprint, not the
network. A residential proxy changes only the variable already proven not to
matter.

The anti-bot industry says the same thing in its own marketing: a clean
residential IP paired with a non-browser TLS handshake is flagged instantly,
because Cloudflare layers JA3/JA4 TLS fingerprinting, HTTP/2 frame ordering and
behavioural signals on top of IP reputation. Their stated recipe is proxy **plus**
a TLS-impersonating client (`curl-impersonate`, `tls-client`) **plus** stealth
browser patches (`undetected-chromedriver`, `playwright-extra-stealth`), and a
CAPTCHA-solving service when a challenge still lands.

That second and third layer is bot-detection bypass by construction. **Not built
here.** Commercial scraper APIs (Apify's Micro Center actor, Actowiz) do exactly
that bypass as a paid service and are a real option if Sean wants one — they just
cost money, which was the thing he wanted to avoid, and they carry the same
posture questions we would be paying someone else to hold.

## What actually works: capture during a human page view

Micro Center has **no official API** (confirmed on their own community forum) and
**no native in-stock or price-drop alert** — only the Insider SMS marketing list.

The working pattern is a tracker whose data capture rides a *genuine human visit*:
a browser extension reads the product page Sean already opened, and the service
tracks it server-side from there. No bypass involved, because a person really did
load the page.

**PriceLasso** (`pricelasso.com`) does this, is free, and lists Micro Center as a
supported store: sign up, install the extension, click its button on the B70
product page, get email alerts on price drops plus price history. Verified
2026-08-26 that the service and its Micro Center support page are live.

Limitation, checked directly: **no public API or webhook** — `/api`, `/docs`,
`/developers`, `/integrations` all 404, and the homepage mentions no API/Zapier
surface. Alerts are email-only. To land them in this stack, relay the alert mail
through n8n (or the `mcp-email` Graph server) into the existing notification
path. That relay is unbuilt and is the natural next step if the alerts prove
useful.

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
