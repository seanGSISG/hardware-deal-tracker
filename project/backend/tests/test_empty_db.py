"""ADR-005 — the app must operate correctly from a fresh/empty catalog.

The 34 seeded items are OPTIONAL starter data. No code path may assume tracked
items exist. These tests boot against an empty database and assert:
  1. Read endpoints (items list, stats, deals) and the poller degrade gracefully
     (no 500s, sensible empties) when zero tracked items exist.
  2. A user-created item then flows end-to-end: poll -> score -> dashboard (deals).
"""
from sqlalchemy import select

from app.models.listing import Listing
from app.models.listing_score import ListingScore
from app.models.tracked_item import TrackedItem
from app.services.ebay.poller import EbayPoller


class _StubClient:
    """Deterministic eBay-shaped response (no network, no randomness)."""

    async def search(self, keywords, **kwargs):
        return {
            "itemSummaries": [
                {
                    "itemId": "empty_db_1",
                    "title": "Fresh DB widget",
                    "price": {"value": "150.00", "currency": "USD"},
                    "shippingOptions": [{"shippingCost": {"value": "0", "currency": "USD"}}],
                    "seller": {"username": "s", "feedbackScore": 500, "feedbackPercentage": "99.0"},
                    "condition": "Used",
                    "conditionId": "3000",
                    "itemWebUrl": "https://www.ebay.com/itm/empty_db_1",
                    "buyingOptions": ["FIXED_PRICE"],
                }
            ],
            "total": 1,
            "offset": 0,
            "limit": 200,
        }


# --- 1. Endpoints + poller degrade gracefully on an empty catalog ----------

async def test_items_list_empty_no_500(client):
    resp = await client.get("/api/v1/items")
    assert resp.status_code == 200
    body = resp.json()
    assert body["items"] == []
    assert body["total"] == 0


async def test_item_stats_empty_no_500(client):
    resp = await client.get("/api/v1/items/stats")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total_items"] == 0
    assert body["enabled_items"] == 0
    assert body["estimated_daily_calls"] == 0


async def test_deals_dashboard_empty_no_500(client):
    resp = await client.get("/api/v1/deals")
    assert resp.status_code == 200
    body = resp.json()
    assert body["deals"] == []
    assert body["total"] == 0


async def test_poller_search_all_on_empty_db_is_graceful(db):
    poller = EbayPoller()
    poller.client = _StubClient()

    result = await poller.search_all(db)

    assert result["items_due"] == 0
    assert result["items_processed"] == 0
    assert result["errors"] == []


# --- 2. User-created item flows poll -> score -> dashboard ------------------

async def test_user_created_item_flows_through_pipeline(db, admin_client):
    # Sanity: truly empty to start.
    pre = (await db.execute(select(TrackedItem))).scalars().all()
    assert pre == []

    # User (admin) creates the very first catalog item from scratch.
    create = await admin_client.post(
        "/api/v1/items",
        json={
            "name": "Bootstrap CPU",
            "keywords": "Bootstrap CPU",
            "category_id": "164",
            "target_price": 120.0,
            "benchmark_median": 300.0,
            "scam_floor": 10.0,
            "search_interval": 600,
            "is_enabled": True,
        },
    )
    assert create.status_code == 200, create.text
    item_id = create.json()["id"]

    # Reload the persisted item and run the poll/score pipeline against it.
    item = (
        await db.execute(select(TrackedItem).where(TrackedItem.id == item_id))
    ).scalar_one()

    poller = EbayPoller()
    poller.client = _StubClient()
    result = await poller.search_item(db, item)
    await db.flush()

    assert result["new_listings"] >= 1

    listings = (
        await db.execute(select(Listing).where(Listing.tracked_item_id == item_id))
    ).scalars().all()
    scores = (
        await db.execute(select(ListingScore).where(ListingScore.tracked_item_id == item_id))
    ).scalars().all()

    assert len(listings) == result["new_listings"]
    assert len(scores) == result["new_listings"]
    # Benchmark came purely from the user-created item (no seed/catalog dependency):
    # $150 total vs $300 benchmark => a strong, surfaced deal.
    for sc in scores:
        assert 0 <= sc.overall_score <= 100
        assert sc.est_fair_value == 300.0
