"""feature-001 story-007: surface the resolved baseline on the price-history API.

TDD: written FIRST. The /price-history/{item_id} response includes the current
ItemPriceBaseline fields (median, q1/q3 IQR band, vs_median_pct, data_points,
source, trend_direction, trend_slope_pct), degrading to null/benchmark when no
snapshot exists. Additive only — existing keys are unchanged.
"""
from datetime import datetime, timedelta

from app.models.item_price_baseline import ItemPriceBaseline
from app.models.listing import Listing
from app.models.price_history import PriceHistory
from app.models.tracked_item import TrackedItem


async def _seed_item(db, **overrides):
    defaults = {
        "name": "EPYC 7F72", "keywords": "EPYC 7F72", "benchmark_median": 350,
        "scam_floor": 10, "search_interval": 600, "is_enabled": True,
    }
    defaults.update(overrides)
    item = TrackedItem(**defaults)
    db.add(item)
    await db.flush()
    return item


async def _seed_history(db, item, totals):
    listing = Listing(
        marketplace_id="m1", tracked_item_id=item.id, title="x", price=100,
        shipping=0, seller="s", url="u", listing_date=datetime.utcnow(),
    )
    db.add(listing)
    await db.flush()
    base = datetime(2026, 5, 1, 12, 0, 0)
    for i, total in enumerate(totals):
        db.add(PriceHistory(
            listing_id=listing.id, tracked_item_id=item.id,
            observed_price=total, shipping=0, total_price=total,
            timestamp=base + timedelta(days=i),
        ))
    await db.flush()


async def test_response_includes_baseline_when_snapshot_exists(client, db):
    item = await _seed_item(db)
    await _seed_history(db, item, [300, 320, 310])
    db.add(ItemPriceBaseline(
        tracked_item_id=item.id, median_price=500.0, avg_price=505.0,
        std_dev=20.0, min_price=460.0, q1=485.0, q3=520.0, data_points=18,
        lookback_days=90, trend_direction="rising", trend_slope_pct=0.12,
        source="price_history",
    ))
    await db.flush()

    resp = await client.get(f"/api/v1/price-history/{item.id}")
    assert resp.status_code == 200
    body = resp.json()
    assert "baseline" in body
    b = body["baseline"]
    assert b["median"] == 500.0
    assert b["q1"] == 485.0
    assert b["q3"] == 520.0
    assert b["data_points"] == 18
    assert b["source"] == "price_history"
    assert b["trend_direction"] == "rising"
    assert b["trend_slope_pct"] == 0.12
    # vs_median_pct = (median - latest_total) / median, latest total is 310.
    assert b["vs_median_pct"] == round((500.0 - 310.0) / 500.0, 4)
    # Existing keys are still present (additive change).
    assert body["count"] == 3
    assert "points" in body and "median_total" in body


async def test_response_degrades_when_no_snapshot(client, db):
    item = await _seed_item(db)
    await _seed_history(db, item, [300, 320, 310])

    resp = await client.get(f"/api/v1/price-history/{item.id}")
    assert resp.status_code == 200
    body = resp.json()
    assert "baseline" in body
    b = body["baseline"]
    # No snapshot: degrade gracefully to nulls + benchmark source.
    assert b["median"] is None
    assert b["source"] == "benchmark"
    assert b["trend_direction"] is None
    assert b["data_points"] == 0
    # Benchmark median still exposed for downstream rendering.
    assert b["benchmark_median"] == 350.0


async def test_benchmark_sourced_snapshot_degrades(client, db):
    item = await _seed_item(db)
    db.add(ItemPriceBaseline(
        tracked_item_id=item.id, median_price=None, data_points=0,
        source="benchmark", trend_direction="stable", trend_slope_pct=0.0,
    ))
    await db.flush()

    resp = await client.get(f"/api/v1/price-history/{item.id}")
    body = resp.json()
    b = body["baseline"]
    assert b["median"] is None
    assert b["source"] == "benchmark"
    assert b["trend_direction"] == "stable"
