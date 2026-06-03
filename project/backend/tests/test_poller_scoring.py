"""story-002: EbayPoller.search_item must score each new listing (ADR-006).

Closes the keystone gap: the poller previously parsed/deduped/persisted Listing
rows but never invoked DealScoringEngine, so nothing was scored for the dashboard
or the notification dispatcher to act on.
"""
from datetime import datetime

from sqlalchemy import select

from app.models.listing import Listing
from app.models.listing_score import ListingScore
from app.models.tracked_item import TrackedItem
from app.services.ebay.poller import EbayPoller


class _StubClient:
    """Returns a fixed eBay-shaped response (no randomness, no network)."""

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
        "name": "EPYC 7F72",
        "keywords": "EPYC 7F72",
        "benchmark_median": 350,
        "scam_floor": 10,
        "search_interval": 600,
        "is_enabled": True,
    }
    defaults.update(overrides)
    item = TrackedItem(**defaults)
    db.add(item)
    await db.flush()
    return item


async def test_search_item_scores_and_persists_each_new_listing(db):
    item = await _add_item(db)
    poller = EbayPoller()

    result = await poller.search_item(db, item)
    await db.flush()

    listings = (await db.execute(select(Listing).where(Listing.tracked_item_id == item.id))).scalars().all()
    scores = (await db.execute(select(ListingScore).where(ListingScore.tracked_item_id == item.id))).scalars().all()

    assert result["new_listings"] >= 1
    assert len(listings) == result["new_listings"]
    # One ListingScore per new listing — the keystone gap this story closes.
    assert len(scores) == result["new_listings"]
    for sc in scores:
        assert 0 <= sc.overall_score <= 100
        assert sc.classification
        assert sc.tracked_item_id == item.id
        assert sc.scam_flag is None  # scam_floor=10 is below any real price


async def test_scam_floor_maps_to_scam_flag(db):
    # An absurdly high scam_floor forces every listing below it -> scam_warning set.
    item = await _add_item(db, scam_floor=100000)
    poller = EbayPoller()

    await poller.search_item(db, item)
    await db.flush()

    scores = (await db.execute(select(ListingScore).where(ListingScore.tracked_item_id == item.id))).scalars().all()
    assert scores, "expected at least one scored listing"
    assert any(sc.scam_flag and "scam floor" in sc.scam_flag for sc in scores)
    assert any(sc.classification == "suspicious" for sc in scores)


async def test_search_item_dispatches_each_scored_listing(db):
    """story-T2.3 hook: poller invokes the dispatcher once per scored listing."""
    item = await _add_item(db)
    poller = EbayPoller()
    poller.client = _StubClient([_raw_item("disp_1", "120"), _raw_item("disp_2", "130")])

    calls = []

    class _SpyDispatcher:
        async def dispatch_for_deal(self, db, listing, score):
            calls.append((listing.id, score["overall_score"]))

    poller.dispatcher = _SpyDispatcher()

    result = await poller.search_item(db, item)
    await db.flush()

    assert result["new_listings"] == 2
    assert len(calls) == 2


async def test_dispatch_failure_is_non_fatal(db):
    """A dispatcher exception must not break the poll/score path."""
    item = await _add_item(db)
    poller = EbayPoller()
    poller.client = _StubClient([_raw_item("safe_1", "120")])

    class _BoomDispatcher:
        async def dispatch_for_deal(self, db, listing, score):
            raise RuntimeError("dispatch boom")

    poller.dispatcher = _BoomDispatcher()

    result = await poller.search_item(db, item)
    await db.flush()

    # Listing + score still persisted despite the dispatch failure.
    assert result["new_listings"] == 1
    scores = (await db.execute(select(ListingScore).where(ListingScore.tracked_item_id == item.id))).scalars().all()
    assert len(scores) == 1


async def test_duplicates_are_not_rescored(db):
    item = await _add_item(db)

    # Pre-existing listing that the next poll will re-encounter as a duplicate.
    db.add(
        Listing(
            marketplace_id="dup_1",
            tracked_item_id=item.id,
            title="already seen",
            price=100,
            shipping=0,
            seller="seller",
            url="https://www.ebay.com/itm/dup_1",
            listing_date=datetime.utcnow(),
        )
    )
    await db.flush()

    poller = EbayPoller()
    poller.client = _StubClient([_raw_item("dup_1", "100"), _raw_item("new_1", "120")])

    result = await poller.search_item(db, item)
    await db.flush()

    scores = (await db.execute(select(ListingScore).where(ListingScore.tracked_item_id == item.id))).scalars().all()

    assert result["new_listings"] == 1
    assert result["duplicates_skipped"] == 1
    # Only the new listing is scored; the pre-existing duplicate is not re-scored.
    assert len(scores) == 1
