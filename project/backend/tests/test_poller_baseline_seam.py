"""feature-001 story-005: _historical_stats_for reads the persisted snapshot.

TDD: written FIRST. When a usable ItemPriceBaseline snapshot exists, the poller
scores new listings against the snapshot baseline (raising data_points-driven
confidence above the catalog-only 0.45 and reflecting the snapshot median in
est_fair_value). With NO snapshot, scores fall back to catalog benchmark exactly
as before (regression guard).
"""
from sqlalchemy import select

from app.models.item_price_baseline import ItemPriceBaseline
from app.models.listing_score import ListingScore
from app.models.tracked_item import TrackedItem
from app.services.ebay.poller import EbayPoller


class _StubClient:
    def __init__(self, items):
        self._items = items

    async def search(self, keywords, **kwargs):
        return {"itemSummaries": self._items, "total": len(self._items), "offset": 0, "limit": 200}


def _raw_item(item_id: str, price: str) -> dict:
    return {
        "itemId": item_id,
        "title": f"Test {item_id}",
        "price": {"value": price, "currency": "USD"},
        "shippingOptions": [{"shippingCost": {"value": "0", "currency": "USD"}}],
        "seller": {"username": "seller", "feedbackScore": 500, "feedbackPercentage": "99.0"},
        "condition": "Used",
        "conditionId": "3000",
        "itemWebUrl": f"https://www.ebay.com/itm/{item_id}",
        "buyingOptions": ["FIXED_PRICE"],
    }


async def _add_item(db, **overrides) -> TrackedItem:
    defaults = {
        "name": "EPYC 7F72", "keywords": "EPYC 7F72", "benchmark_median": 350,
        "scam_floor": 10, "search_interval": 600, "is_enabled": True,
    }
    defaults.update(overrides)
    item = TrackedItem(**defaults)
    db.add(item)
    await db.flush()
    return item


async def test_usable_snapshot_drives_scoring_and_confidence(db):
    item = await _add_item(db)
    # A usable snapshot with a median well above the listing price (a good deal),
    # and enough data_points to push confidence past the catalog-only 0.45.
    db.add(ItemPriceBaseline(
        tracked_item_id=item.id, median_price=500.0, avg_price=500.0,
        std_dev=50.0, min_price=400.0, q1=480.0, q3=520.0, data_points=25,
        lookback_days=90, trend_direction="stable", trend_slope_pct=0.0,
        source="price_history",
    ))
    await db.flush()

    poller = EbayPoller()
    poller.client = _StubClient([_raw_item("snap_1", "300")])
    await poller.search_item(db, item)
    await db.flush()

    score = (
        await db.execute(select(ListingScore).where(ListingScore.tracked_item_id == item.id))
    ).scalar_one()
    # est_fair_value reflects the snapshot median (500), not the catalog benchmark (350).
    assert float(score.est_fair_value) == 500.0
    # data_points=25 -> confidence 0.80 (>20 bucket), above catalog-only 0.45.
    assert float(score.confidence) > 0.45


async def test_no_snapshot_falls_back_to_catalog_benchmark(db):
    item = await _add_item(db)  # no ItemPriceBaseline row
    poller = EbayPoller()
    poller.client = _StubClient([_raw_item("nosnap_1", "300")])
    await poller.search_item(db, item)
    await db.flush()

    score = (
        await db.execute(select(ListingScore).where(ListingScore.tracked_item_id == item.id))
    ).scalar_one()
    # Falls back to catalog benchmark_median (350); confidence is the catalog-only 0.45.
    assert float(score.est_fair_value) == 350.0
    assert float(score.confidence) == 0.45


async def test_benchmark_sourced_snapshot_is_not_used(db):
    # A degraded (source='benchmark', null stats) snapshot must NOT be used; the
    # engine path stays identical to catalog-only fallback.
    item = await _add_item(db)
    db.add(ItemPriceBaseline(
        tracked_item_id=item.id, median_price=None, data_points=0,
        source="benchmark", trend_direction="stable", trend_slope_pct=0.0,
    ))
    await db.flush()

    poller = EbayPoller()
    poller.client = _StubClient([_raw_item("bench_1", "300")])
    await poller.search_item(db, item)
    await db.flush()

    score = (
        await db.execute(select(ListingScore).where(ListingScore.tracked_item_id == item.id))
    ).scalar_one()
    assert float(score.est_fair_value) == 350.0  # catalog benchmark, not the null snapshot
    assert float(score.confidence) == 0.45
