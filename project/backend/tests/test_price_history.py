"""story-1 (feature-006): capture a PriceHistory point per listing each poll tick."""
from sqlalchemy import select

from app.models.listing import Listing
from app.models.price_history import PriceHistory
from app.models.tracked_item import TrackedItem
from app.services.ebay.poller import EbayPoller


async def _add_item(db) -> TrackedItem:
    item = TrackedItem(
        name="EPYC 7F72",
        keywords="EPYC 7F72",
        benchmark_median=350,
        scam_floor=10,
        search_interval=600,
        is_enabled=True,
    )
    db.add(item)
    await db.flush()
    return item


async def test_search_item_records_price_history_per_listing(db):
    item = await _add_item(db)
    poller = EbayPoller()

    result = await poller.search_item(db, item)
    await db.flush()

    history = (
        await db.execute(select(PriceHistory).where(PriceHistory.tracked_item_id == item.id))
    ).scalars().all()
    listings = (
        await db.execute(select(Listing).where(Listing.tracked_item_id == item.id))
    ).scalars().all()

    # One price point per new listing in this poll snapshot.
    assert result["new_listings"] >= 1
    assert len(history) == result["new_listings"]
    assert len(history) == len(listings)
    for p in history:
        assert float(p.total_price) == round(float(p.observed_price) + float(p.shipping), 2)
        assert p.listing_id is not None
