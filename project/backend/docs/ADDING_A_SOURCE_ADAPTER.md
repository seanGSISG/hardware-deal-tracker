# How to add a new source adapter

The multi-source ingestion layer (feature-005) lets you add a new price/listing
source without touching the scheduler, scoring engine, dedup, or notifications.
Everything funnels through one contract.

## The contract

`app/services/sources/base.py` defines:

- **`NormalizedListing`** — the single record every source maps to:
  `source`, `source_listing_id`, `title`, `url`, `price`, `currency`, `shipping`,
  `condition`, `availability`, `seller`, `catalog_item_id`, `raw_payload`,
  `fetched_at`. `.total` = `price + shipping`.
- **`SourceAdapter`** (ABC) — set a class-level `source` identity and implement
  `async def search(self, catalog_item) -> list[NormalizedListing]`.

Dedup keys on `(source, source_listing_id)` (see `DeduplicationEngine`), so the
same raw id under two sources is NOT a duplicate — set `source_listing_id` to the
source's stable id (eBay item id, Shopify variant id, etc.).

## Steps

1. **Create the adapter** in `app/services/sources/<name>.py`:
   - Subclass `SourceAdapter`, set `source = "<name>"`.
   - Take an **injected transport** in `__init__` (a small object/Protocol with an
     async fetch method). Never hard-code live HTTP in the adapter — that makes it
     untestable and unmockable.
   - Implement `search()` to fetch via the transport and map each result to a
     `NormalizedListing`.

2. **Add a real transport** in `app/services/sources/<name>_transport.py` (an
   `httpx`-based default is fine). Tests inject a fake; production injects the real
   one. Always check the source's robots.txt / ToS before enabling it.

3. **Rate-limit it.** Use `SourceRateBudget` (`app/services/sources/rate_budget.py`)
   for a polite, self-imposed per-source daily bucket — **separate** from eBay's
   5000/day `RateBudgetManager`. Configure the bucket in the adapter's `__init__`.

4. **Gate it behind config.** Add `ENABLE_<SOURCE>` (default `False`) and a
   `<SOURCE>_DAILY_LIMIT` to `app/core/config.py`. Default OFF for anything
   ToS-sensitive or anti-bot defended.

5. **Write tests** (`tests/test_<name>_adapter.py`), test-first:
   - `isinstance(adapter, SourceAdapter)` and `adapter.source` is correct.
   - `search()` returns `NormalizedListing`s with the right fields (use a **fake
     transport** — never a live call).
   - Rate-bucket exhaustion stops fetching; disabled-by-default returns `[]`.

## Patterns / gotchas

- **Benchmark-only sources** (e.g. `PcPartPickerAdapter`): keep their rows OUT of
  the scoring/dedup/notification pipeline. Make `search()` return `[]` and expose a
  separate method (e.g. `refresh_benchmark(catalog_item)`) that updates
  `TrackedItem.benchmark_median` + a 'vs retail' delta. Condition is always `new`.
  Add a **circuit breaker** for anti-bot sources so repeated 403s stop hammering.
- **Generic per-source adapters** (e.g. `ShopifyJsonLdAdapter`): keep the adapter
  data-driven via a config dataclass (`source`, `base_url`, `merchant`, ...). One
  class serves many retailers (TechMikeNY → UnixSurplus → ServerMonkey) — only the
  config differs.
- **eBay** is the reference implementation: `EbayBrowseAdapter`
  (`app/services/sources/ebay.py`) wraps the existing client+parser and stashes the
  rich eBay-shaped row in `raw_payload["_listing_row"]` so `EbayPoller` can persist
  a full `Listing` and score it.
- New Python dependency? Add it to `backend/pyproject.toml`. New DB column (like
  `tracked_items.pcpp_product_id`)? Add an Alembic migration.

## Existing adapters

| Adapter | File | Routed to scoring? | Notes |
|---|---|---|---|
| `EbayBrowseAdapter` | `sources/ebay.py` | yes (via `EbayPoller`) | first adapter; 5000/day eBay budget |
| `PcPartPickerAdapter` | `sources/pcpartpicker.py` | **no** (benchmark only) | gated OFF, own ≤200/day bucket, circuit breaker |
| `ShopifyJsonLdAdapter` | `sources/shopify.py` | yes (normalized) | generic, per-source config, own bucket |
