"""story-2 (feature-006): price-history time-series API."""
from datetime import datetime, timedelta

from app.models.listing import Listing
from app.models.price_history import PriceHistory
from app.models.tracked_item import TrackedItem


async def _seed(db):
    item = TrackedItem(
        name="EPYC 7F72", keywords="EPYC 7F72", benchmark_median=350,
        scam_floor=10, search_interval=600, is_enabled=True,
    )
    db.add(item)
    await db.flush()
    listing = Listing(
        marketplace_id="m1", tracked_item_id=item.id, title="x", price=100,
        shipping=0, seller="s", url="u", listing_date=datetime.utcnow(),
    )
    db.add(listing)
    await db.flush()
    base = datetime(2026, 5, 1, 12, 0, 0)
    for i, total in enumerate([100, 300, 200]):
        db.add(PriceHistory(
            listing_id=listing.id, tracked_item_id=item.id,
            observed_price=total, shipping=0, total_price=total,
            timestamp=base + timedelta(days=i),
        ))
    await db.flush()
    return item


async def test_price_history_series_and_summary(client, db):
    item = await _seed(db)

    resp = await client.get(f"/api/v1/price-history/{item.id}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["count"] == 3
    assert len(body["points"]) == 3
    # Points are time-ordered ascending.
    ts = [p["timestamp"] for p in body["points"]]
    assert ts == sorted(ts)
    # Summary stats over the window.
    assert body["median_total"] == 200.0
    assert body["latest_total"] == 200.0  # the last-by-timestamp point (i=2 -> total 200)


async def test_price_history_missing_item_404(client):
    resp = await client.get("/api/v1/price-history/9999")
    assert resp.status_code == 404


async def test_price_history_empty_item_is_graceful(client, db):
    item = TrackedItem(
        name="Empty", keywords="none", benchmark_median=100,
        scam_floor=5, search_interval=600, is_enabled=True,
    )
    db.add(item)
    await db.flush()

    resp = await client.get(f"/api/v1/price-history/{item.id}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["count"] == 0
    assert body["points"] == []
    assert body["median_total"] is None
