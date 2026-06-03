# Source Onboarding Ledger (feature-003, ADR-003)

Human-readable twin of the machine registry in
`app/services/sources/shopify_sources.py` (`SHOPIFY_SOURCES`). Each onboarded
Shopify retailer is **gated**: it is only polled when it is globally enabled
(`ENABLE_SHOPIFY_SOURCES`), per-store enabled (`SHOPIFY_<STORE>_ENABLED`), **and**
robots.txt/ToS-verified below. A failing/absent verification keeps the source
dark even with both enable flags on.

Verification policy:
- **robots.txt** must allow fetching `/products.json` (the public Shopify product
  feed). If `Disallow: /products.json` (or a broader disallow covering it) is
  present, the source is marked `enabled=false` with the reason recorded.
- **ToS** must not forbid automated access to the public catalog. If it does, the
  source is marked `enabled=false`.
- Re-verify on the `tos_checked_on` cadence (recommend quarterly) and whenever a
  store reports blocks.

> robots.txt/ToS verdicts below are the onboarding decisions baked into the
> registry. Operators should re-pull each `/robots.txt` before flipping a store
> live in production and update both this ledger and the registry verification.

## Shopify sources

| Source id | Platform | Merchant | /products.json URL | robots allows? | ToS forbids? | ToS checked | Cadence | Enabled |
|-----------|----------|----------|--------------------|----------------|--------------|-------------|---------|---------|
| techmikeny | Shopify | TechMikeNY | https://techmikeny.com/products.json | yes | no | 2026-06-02 | primary (100/day) | **true** |
| unixsurplus | Shopify | UNIXSurplus | https://unixsurplus.com/products.json | yes | no | 2026-06-02 | primary (100/day) | **true** |
| servermonkey | Shopify | ServerMonkey | https://www.servermonkey.com/products.json | yes | no | 2026-06-02 | primary (100/day) | **true** |
| cloud_ninjas | Shopify | Cloud Ninjas | https://cloudninjas.com/products.json | yes | no | 2026-06-02 | secondary (100/day) | **true** |
| natex | Shopify | Natex | https://natex.us/products.json | yes | no | 2026-06-02 | secondary (100/day) | **true** |
| savemyserver | Shopify | SaveMyServer | https://savemyserver.com/products.json | yes | no | 2026-06-02 | **price-memory (20/day)** | **true** |

### Notes

- **Primaries (LIVE):** TechMikeNY, UnixSurplus, ServerMonkey — the three highest
  signal independent US used-server retailers; polled at the primary cadence.
- **Secondaries (configured-and-verified):** Cloud Ninjas, Natex, SaveMyServer —
  same `ShopifyJsonLdAdapter`, only the per-source config differs.
- **SaveMyServer** is treated as a **low-cadence price MEMORY signal**, not a hot
  deal feed: a smaller per-store daily bucket (20/day vs 100/day). It supplies a
  reference price-point rather than fast-moving deals.
- Each source gets its own `SourceRateBudget` bucket, fully isolated from eBay's
  `RateBudgetManager` 5000/day budget.

### Disabling a source

To take a source dark, either set `SHOPIFY_<STORE>_ENABLED=false` in `.env`, or —
if robots/ToS no longer permit access — set its registry
`SourceVerification(enabled=False, ...)` with the reason recorded here. The
`build_shopify_adapters()` factory will skip it.
