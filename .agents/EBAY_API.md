# eBay API Integration

> Everything about eBay API interaction, rate limiting, mocking, and the polling system. Read this when working on search, polling, or API budget code.

---

## Overview

The system searches eBay's **Browse API** (not the decommissioned Finding API) for listings matching tracked hardware items. All API calls are rate-limited through a 4-layer protection system.

Two clients exist:
- **EbayBrowseClient** — Real eBay API (production)
- **MockEbayClient** — Generates realistic mock listings (development)

Switch via `USE_MOCK_EBAY` env var.

---

## Service Files

| File | Purpose |
|------|---------|
| `services/ebay/client.py` | Real eBay Browse API client (OAuth2 app-token auth) |
| `services/ebay/mock.py` | Mock client with realistic price distributions |
| `services/ebay/parser.py` | Normalizes raw API responses into Listing models |
| `services/ebay/dedup.py` | Filters duplicate listings by eBay item ID |
| `services/ebay/rate_budget.py` | 4-layer rate limiting with Redis |
| `services/ebay/poller.py` | Async scheduler that orchestrates searches |
| `services/ebay/catalog.py` | 34 hardware SKUs with search keywords and pricing | See [CATALOG.md](CATALOG.md) |

---

## Client Selection

```python
# services/ebay/__init__.py or similar bootstrap
from app.core.config import settings
from app.services.ebay.client import EbayBrowseClient
from app.services.ebay.mock import MockEbayClient

if settings.USE_MOCK_EBAY:
    client = MockEbayClient()
else:
    client = EbayBrowseClient(
        app_id=settings.EBAY_APP_ID,
        cert_id=settings.EBAY_CERT_ID,
    )
```

---

## EbayBrowseClient (Production)

### Authentication

Uses **OAuth2 Application Token** (client credentials flow):
1. POST to eBay identity endpoint with base64(client_id:client_secret)
2. Receive access token (valid 2 hours)
3. Token auto-refreshes before expiry

### Search Method

```python
async def search_item(
    self,
    keywords: str,
    category_id: str | None = None,
    min_price: Decimal | None = None,
    max_price: Decimal | None = None,
    limit: int = 50,
    sort: str = "-price",  # Descending price
) -> list[dict]:
    """Search eBay Browse API. Returns raw API response dicts."""
```

Maps to: `GET https://api.ebay.com/buy/browse/v1/item_summary/search?q={keywords}&category_ids={id}&filter=price:[{min}..{max}]&sort={sort}&limit={limit}`

### Error Handling

| Error | Behavior |
|-------|----------|
| HTTP 401 | Refresh OAuth token, retry once |
| HTTP 429 (rate limit) | Back off 60s, log warning |
| HTTP 5xx | Retry up to 3x with exponential backoff |
| Network timeout | Retry once, then mark call as failed |

---

## MockEbayClient (Development)

Generates realistic mock listings without API calls. Perfect for frontend development and testing.

### Behavior

- Returns 5-25 listings per search (random)
- Prices distributed around catalog `benchmark_median` with ±30% variance
- 10% of listings are "scams" (below `scam_floor`)
- 20% are auctions (with end dates), 80% Buy-It-Now
- Sellers have realistic ratings (90-100% positive)
- Deterministic seed for reproducible results

### Configuration

| Env Var | Effect |
|---------|--------|
| `MOCK_PRICE_VARIANCE` | Price spread (default: 0.3 = ±30%) |
| `MOCK_SCAM_RATIO` | % of scam listings (default: 0.1) |
| `MOCK_LISTING_COUNT_MIN` | Minimum listings per search (default: 5) |
| `MOCK_LISTING_COUNT_MAX` | Maximum listings per search (default: 25) |

---

## ListingParser

Transforms raw eBay API responses into normalized `Listing` model dicts.

```python
# Input: eBay API response
{
    "itemId": "v1|123456789|0",
    "title": "AMD EPYC 7F72 24-Core 3.2GHz Processor",
    "price": {"value": "1850.00", "currency": "USD"},
    "seller": {"username": "serverparts_inc", "feedbackScore": 15000},
    ...
}

# Output: Normalized dict ready for DB insert
{
    "ebay_item_id": "123456789",
    "title": "AMD EPYC 7F72 24-Core 3.2GHz Processor",
    "price": Decimal("1850.00"),
    "seller_name": "serverparts_inc",
    "seller_feedback_count": 15000,
    ...
}
```

Handles:
- eBay item ID normalization (strips `v1|...|0` prefix)
- Price parsing (string → Decimal)
- Shipping cost extraction (defaults to 0)
- Condition mapping (eBay enum → canonical values)
- URL generation (item web URL)
- Image URL extraction (first image)

---

## DeduplicationEngine

Prevents saving the same eBay listing multiple times.

```python
async def filter_new(
    self,
    db: AsyncSession,
    item_id: int,
    listings: list[dict],
) -> list[dict]:
    """Return only listings whose ebay_item_id hasn't been seen for this tracked_item."""
```

- Checks `listings` table for existing `ebay_item_id` per `tracked_item_id`
- Uses Redis SET for fast lookups (falls back to DB query)
- Returns only new listings for scoring + saving

---

## RateBudgetManager (4-Layer Protection)

Central nervous system of API consumption. Every search call must go through this.

### Layer 1: Per-Item Interval

Each `TrackedItem` has `search_interval` (seconds). An item is only searched if `now - last_searched ≥ search_interval`.

### Layer 2: Redis Daily Counter

- Key: `ebay_api_calls_{date}` (e.g., `ebay_api_calls_2025_05_16`)
- Value: integer count of API calls today
- TTL: 25 hours (auto-expires next day)
- Atomically incremented via `INCR`

### Layer 3: Priority-Based Skipping

When `calls_today ≥ EBAY_NEAR_LIMIT_THRESHOLD` (default 4000):
- Skip P3 items entirely
- If ≥ 4200: also skip P2
- If ≥ 4500: also skip P1
- P0 items always searched unless hard stop

### Layer 4: Hard Stop

When `calls_today ≥ EBAY_DAILY_CALL_LIMIT - EBAY_CALL_BUFFER` (default 4800):
- All searches halted
- Logged as critical warning
- Resumes after counter resets (next day or manual Redis delete)

### Code Pattern

```python
from app.services.ebay.rate_budget import RateBudgetManager

budget = RateBudgetManager(redis_client)

async def poll_item(item: TrackedItem):
    # Layer 1: Interval check (in poller)
    if not item_is_due(item):
        return

    # Layer 2-4: Budget check
    can_search, reason = await budget.can_search(item.priority_tier)
    if not can_search:
        logger.warning(f"Skipping {item.name}: {reason}")
        return

    # Execute search
    listings = await client.search_item(item.search_keywords)

    # Record the call
    await budget.record_call()
```

### Fallback Mode

If Redis is unavailable:
- Uses in-memory Python counter
- Counter resets on process restart (acceptable for dev)
- Full rate limiting still active but not persisted

---

## EbayPoller (Scheduler)

### How It Works

```python
class EbayPoller:
    """Runs every 60 seconds. Checks which items are due, searches in priority order."""

    async def tick(self):
        for tier in ["P0", "P1", "P2", "P3"]:
            due_items = self.get_due_items(tier)
            for item in due_items:
                if not await self.budget.can_search(tier):
                    continue  # Rate limit hit, skip

                listings = await self.client.search_item(item.search_keywords)
                parsed = [self.parser.normalize(l) for l in listings]
                new_listings = await self.dedup.filter_new(item.id, parsed)

                for listing_data in new_listings:
                    listing = await self.save_listing(item.id, listing_data)
                    score = await self.scorer.score(listing)
                    await self.save_score(listing.id, score)

                    if score.total_score >= self.alert_threshold:
                        await self.notify(listing, score)

                await self.budget.record_call()
                await self.update_last_searched(item)
```

### Scheduling

- Background task started on FastAPI startup (`@app.on_event("startup")`)
- Runs every 60 seconds via `asyncio.create_task()` loop
- Graceful shutdown on FastAPI stop event

### On-Demand Search

Users can trigger one-off searches via `GET /search?q=...` which bypasses the poller but still respects rate budget.

---

## Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `USE_MOCK_EBAY` | `true` | Use mock instead of real eBay API |
| `EBAY_APP_ID` | — | eBay App ID (production only) |
| `EBAY_CERT_ID` | — | eBay Cert ID (production only) |
| `EBAY_DEV_ID` | — | eBay Dev ID (legacy, may not be needed) |
| `EBAY_REDIRECT_URI` | — | OAuth redirect (production only) |
| `EBAY_DAILY_CALL_LIMIT` | `5000` | Hard daily ceiling |
| `EBAY_CALL_BUFFER` | `200` | Safety buffer before hard stop |
| `EBAY_NEAR_LIMIT_THRESHOLD` | `4000` | Start skipping low-priority items |
| `REDIS_URL` | — | Redis connection for rate counter |

---

## Adding a New eBay Integration Feature

1. **New search parameter**: Edit `EbayBrowseClient.search_item()` signature + query builder
2. **New response field**: Edit `ListingParser.normalize()` + `Listing` model + migration
3. **New rate limit behavior**: Edit `RateBudgetManager.can_search()`
4. **New mock behavior**: Edit `MockEbayClient.generate_listings()`
5. **New polling logic**: Edit `EbayPoller.tick()`
