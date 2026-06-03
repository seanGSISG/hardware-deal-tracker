"""feature-001 story-004: ScoringBaselineService compute/degrade/persist.

TDD: written FIRST. The service assembles price points (fetch_sold_comps seam ->
PriceHistory fallback), runs the story-001 stats + story-002 trend, decides the
snapshot `source`, and upserts the single current ItemPriceBaseline per item.
"""
from datetime import datetime, timedelta

from sqlalchemy import func, select

from app.models.item_price_baseline import ItemPriceBaseline
from app.models.listing import Listing
from app.models.price_history import PriceHistory
from app.models.tracked_item import TrackedItem
from app.services.scoring.baseline_service import ScoringBaselineService


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


async def _seed_history(db, item, totals, *, days_back_start=10):
    listing = Listing(
        marketplace_id="m1", tracked_item_id=item.id, title="x", price=100,
        shipping=0, seller="s", url="u", listing_date=datetime.utcnow(),
    )
    db.add(listing)
    await db.flush()
    base = datetime.utcnow() - timedelta(days=days_back_start)
    for i, total in enumerate(totals):
        db.add(PriceHistory(
            listing_id=listing.id, tracked_item_id=item.id,
            observed_price=total, shipping=0, total_price=total,
            timestamp=base + timedelta(days=i),
        ))
    await db.flush()


async def test_refresh_from_price_history_persists_stats(db):
    item = await _add_item(db)
    # 8 tight points -> survives Tukey, >= BASELINE_MIN_POINTS(5).
    await _seed_history(db, item, [300, 305, 295, 310, 290, 300, 308, 302])

    svc = ScoringBaselineService()
    await svc.refresh_item(db, item)
    await db.flush()

    row = (
        await db.execute(select(ItemPriceBaseline).where(ItemPriceBaseline.tracked_item_id == item.id))
    ).scalar_one()
    assert row.source == "price_history"
    assert row.data_points == 8
    # median of the 8 tight points lands near 300.
    assert 295 <= float(row.median_price) <= 305
    assert float(row.min_price) == 290.0
    assert row.computed_at is not None
    assert row.lookback_days == 90


async def test_fallback_to_benchmark_when_insufficient_points(db):
    item = await _add_item(db)
    # Only 2 points -> below BASELINE_MIN_POINTS -> not a usable comps baseline.
    await _seed_history(db, item, [300, 310])

    svc = ScoringBaselineService()
    await svc.refresh_item(db, item)
    await db.flush()

    row = (
        await db.execute(select(ItemPriceBaseline).where(ItemPriceBaseline.tracked_item_id == item.id))
    ).scalar_one_or_none()
    # Either no usable snapshot, or one explicitly marked benchmark (no usable median
    # from comps) so scoring degrades to catalog benchmark_median.
    if row is not None:
        assert row.source not in ("price_history", "sold_comps")


async def test_refresh_is_idempotent_per_item(db):
    item = await _add_item(db)
    await _seed_history(db, item, [300, 305, 295, 310, 290, 300, 308, 302])
    svc = ScoringBaselineService()

    await svc.refresh_item(db, item)
    await db.flush()
    await svc.refresh_item(db, item)
    await db.flush()

    count = (
        await db.execute(
            select(func.count()).select_from(ItemPriceBaseline)
            .where(ItemPriceBaseline.tracked_item_id == item.id)
        )
    ).scalar_one()
    assert count == 1  # upsert, not duplicate


async def test_trend_is_persisted(db):
    item = await _add_item(db)
    # Clearly rising recent points within the trend window.
    await _seed_history(db, item, [280, 290, 300, 310, 320, 330, 340, 350], days_back_start=8)
    svc = ScoringBaselineService()
    await svc.refresh_item(db, item)
    await db.flush()

    row = (
        await db.execute(select(ItemPriceBaseline).where(ItemPriceBaseline.tracked_item_id == item.id))
    ).scalar_one()
    assert row.trend_direction in ("rising", "falling", "stable")
    assert row.trend_slope_pct is not None
    assert row.trend_direction == "rising"


async def test_fetch_sold_comps_is_swappable_and_returns_empty_today(db):
    item = await _add_item(db)
    svc = ScoringBaselineService()
    comps = await svc.fetch_sold_comps(item)
    assert comps == []


async def test_fetch_sold_comps_swap_drives_sold_comps_source(db):
    """Swapping fetch_sold_comps to real comps must not require changing the math."""
    item = await _add_item(db)
    svc = ScoringBaselineService()

    async def _fake_comps(_item):
        return [300.0, 305.0, 295.0, 310.0, 290.0, 300.0, 308.0]

    svc.fetch_sold_comps = _fake_comps
    await svc.refresh_item(db, item)
    await db.flush()

    row = (
        await db.execute(select(ItemPriceBaseline).where(ItemPriceBaseline.tracked_item_id == item.id))
    ).scalar_one()
    assert row.source == "sold_comps"
    assert row.data_points == 7
