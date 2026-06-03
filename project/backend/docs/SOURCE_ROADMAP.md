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
| 6 Shopify retailers | **LIVE** | Scored deal feed | TechMikeNY, UnixSurplus, ServerMonkey (primaries) + Cloud Ninjas, Natex, SaveMyServer (SaveMyServer = low-cadence price memory). Per-source robots/ToS gate + own rate bucket. See `SOURCE_ONBOARDING.md`. |
| PCPartPicker | **OFF (gated)** | New-retail benchmark only | Never scored; residential egress + circuit breaker. See `PCPARTPICKER_EGRESS.md` + `PCPP_MAPPING.md`. |
| Amazon PA-API | **DEFERRED (NO-GO MVP3)** | (future) new-retail benchmark | Associates affiliate-sales quota gate. See below. |
| Micro Center | **DEFERRED (NO-GO MVP3)** | (future) regional benchmark | No public API + anti-bot + in-store-only pricing. See below. |

## Amazon PA-API — NO-GO for MVP3 (reconsider MVP4)

PA-API 5.0 access is tied to an **Amazon Associates** account that must generate
**qualifying affiliate sales** to keep its request quota; new accounts get a small
quota that is **revoked if no sales occur within ~180 days**, and throttling
scales with sales volume. A price tracker with no storefront cannot reliably keep
credentials provisioned, so PA-API is an unstable foundation today. **Unblock
path (MVP4):** stand up an affiliate-link surface (e.g. "buy on Amazon" CTAs)
producing qualifying sales, then add Amazon as a *new-retail benchmark* source
(reference-only, like PCPartPicker) — not a scored deal feed.

## Micro Center — NO-GO for MVP3 (reconsider MVP4)

No public API, strong anti-bot protection, and **store-/region-scoped, often
in-store-only** pricing that doesn't map onto a national ship-anywhere catalog.
**Reconsideration trigger (MVP4):** an official feed/API or a compliant aggregator;
if revived it would be a **regional new-retail benchmark** behind the same
residential-egress + circuit-breaker posture, never a scored hot-deal feed.

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
