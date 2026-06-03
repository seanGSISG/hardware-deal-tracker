"""story-3: fan Shopify adapters into the poll path.

The poller fans out across the eBay adapter + every enabled+verified Shopify
adapter. Shopify NormalizedListings flow through the SAME pipeline as eBay:
dedup on (source, source_listing_id) -> persist Listing (carrying its source) ->
score -> PriceHistory. Each Shopify source draws from its OWN rate bucket,
isolated from eBay's 5000/day budget, and one source's failure never aborts the
others (graceful degradation).
"""
from sqlalchemy import select

from app.models.listing import Listing
from app.models.listing_score import ListingScore
from app.models.price_history import PriceHistory
from app.models.tracked_item import TrackedItem
from app.services.ebay.poller import EbayPoller
from app.services.sources.base import NormalizedListing


class _StubEbayClient:
    def __init__(self, items):
        self._items = items

    async def search(self, keywords, **kwargs):
        return {"itemSummaries": self._items, "total": len(self._items), "offset": 0, "limit": 200}


def _raw_ebay(item_id: str, price: str) -> dict:
    return {
        "itemId": item_id,
        "title": f"eBay {item_id}",
        "price": {"value": price, "currency": "USD"},
        "shippingOptions": [{"shippingCost": {"value": "0", "currency": "USD"}}],
        "seller": {"username": "ebayseller", "feedbackScore": 500, "feedbackPercentage": "99.0"},
        "condition": "Used",
        "conditionId": "3000",
        "itemWebUrl": f"https://www.ebay.com/itm/{item_id}",
        "buyingOptions": ["FIXED_PRICE"],
    }


class _StubShopifyAdapter:
    """A minimal SourceAdapter that yields canned NormalizedListings."""

    def __init__(self, source: str, listings: list[NormalizedListing], fail: bool = False):
        self.source = source
        self._listings = listings
        self._fail = fail
        self.calls = 0

    async def search(self, catalog_item):
        self.calls += 1
        if self._fail:
            raise RuntimeError(f"{self.source} boom")
        return self._listings


def _nl(source: str, sid: str, price: float, catalog_item_id: int) -> NormalizedListing:
    return NormalizedListing(
        source=source,
        source_listing_id=sid,
        title=f"{source} {sid}",
        url=f"https://{source}.example/products/{sid}",
        price=price,
        currency="USD",
        shipping=0.0,
        condition="Used",
        seller=source,
        catalog_item_id=catalog_item_id,
    )


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


def test_normalized_listing_to_listing_row_round_trips():
    nl = _nl("techmikeny", "v1", 1499.0, catalog_item_id=42)
    row = nl.to_listing_row()
    assert row["source"] == "techmikeny"
    assert row["marketplace_id"] == "v1"
    assert row["tracked_item_id"] == 42
    assert row["price"] == 1499.0
    assert row["seller"] == "techmikeny"
    assert row["url"].endswith("/v1")
    assert row["listing_date"] is not None
    # Buildable as a Listing.
    Listing(**row)


async def test_shopify_listings_are_persisted_scored_and_priced(db):
    item = await _add_item(db)
    poller = EbayPoller()
    poller.client = _StubEbayClient([_raw_ebay("e1", "300")])
    poller.shopify_adapters = [
        _StubShopifyAdapter("techmikeny", [_nl("techmikeny", "tm1", 320.0, item.id)]),
    ]

    result = await poller.search_item(db, item)
    await db.flush()

    listings = (await db.execute(select(Listing).where(Listing.tracked_item_id == item.id))).scalars().all()
    sources = {ll.source for ll in listings}
    assert "ebay" in sources
    assert "techmikeny" in sources

    # Each new listing is scored + gets a price-history point (same path as eBay).
    scores = (await db.execute(select(ListingScore).where(ListingScore.tracked_item_id == item.id))).scalars().all()
    hist = (await db.execute(select(PriceHistory).where(PriceHistory.tracked_item_id == item.id))).scalars().all()
    assert len(scores) == len(listings)
    assert len(hist) == len(listings)
    assert result["new_listings"] == len(listings)


async def test_cross_source_dedup_same_id_different_source(db):
    item = await _add_item(db)
    # Pre-seed an eBay listing with id "shared".
    db.add(
        Listing(
            source="ebay", marketplace_id="shared", tracked_item_id=item.id,
            title="ebay shared", price=300, shipping=0, seller="s",
            url="https://ebay/shared", listing_date=__import__("datetime").datetime.utcnow(),
        )
    )
    await db.flush()

    poller = EbayPoller()
    poller.client = _StubEbayClient([])  # no new eBay rows
    poller.shopify_adapters = [
        # Same id under a different source -> NOT a duplicate.
        _StubShopifyAdapter("techmikeny", [_nl("techmikeny", "shared", 290.0, item.id)]),
    ]

    result = await poller.search_item(db, item)
    await db.flush()

    tm = (await db.execute(
        select(Listing).where(Listing.source == "techmikeny", Listing.marketplace_id == "shared")
    )).scalar_one_or_none()
    assert tm is not None  # the techmikeny row persisted despite the eBay id clash
    assert result["duplicates_skipped"] == 0


async def test_one_source_failure_does_not_abort_others(db):
    item = await _add_item(db)
    poller = EbayPoller()
    poller.client = _StubEbayClient([_raw_ebay("e1", "300")])
    poller.shopify_adapters = [
        _StubShopifyAdapter("natex", [], fail=True),               # explodes
        _StubShopifyAdapter("unixsurplus", [_nl("unixsurplus", "u1", 280.0, item.id)]),
    ]

    result = await poller.search_item(db, item)
    await db.flush()

    listings = (await db.execute(select(Listing).where(Listing.tracked_item_id == item.id))).scalars().all()
    sources = {ll.source for ll in listings}
    # eBay + unixsurplus survived; natex contributed nothing but did not abort.
    assert "ebay" in sources
    assert "unixsurplus" in sources
    assert "natex" not in sources
    # search_all-style per-source error is surfaced without aborting.
    assert any(e.get("source") == "natex" for e in result.get("source_errors", []))


async def test_shopify_bucket_isolated_from_ebay_budget(db):
    """A Shopify source hitting its daily limit short-circuits ONLY itself."""
    item = await _add_item(db)
    # daily_limit=0 means the real adapter would refuse; emulate by an adapter
    # whose bucket is exhausted -> returns [] (no contribution) while eBay runs.
    transport_listings: list[NormalizedListing] = [_nl("servermonkey", "s1", 350.0, item.id)]

    class _ExhaustedShopify:
        source = "servermonkey"

        async def search(self, catalog_item):
            return []  # bucket exhausted

    poller = EbayPoller()
    poller.client = _StubEbayClient([_raw_ebay("e1", "300")])
    poller.shopify_adapters = [_ExhaustedShopify()]

    result = await poller.search_item(db, item)
    await db.flush()

    listings = (await db.execute(select(Listing).where(Listing.tracked_item_id == item.id))).scalars().all()
    sources = {ll.source for ll in listings}
    assert sources == {"ebay"}  # eBay still callable; Shopify contributed nothing
    assert result["new_listings"] == len(listings)
    _ = transport_listings  # documents what an un-exhausted source would have added


async def test_deals_api_surfaces_per_listing_source(db, client):
    """feature-005 badging: the deals API exposes each listing's `source`."""
    item = await _add_item(db)
    poller = EbayPoller()
    poller.client = _StubEbayClient([_raw_ebay("e1", "300")])
    poller.shopify_adapters = [
        _StubShopifyAdapter("techmikeny", [_nl("techmikeny", "tm1", 320.0, item.id)]),
    ]
    await poller.search_item(db, item)
    await db.commit()

    resp = await client.get("/api/v1/deals", params={"min_score": 0, "max_score": 100})
    assert resp.status_code == 200
    deals = resp.json()["deals"]
    sources = {d.get("source") for d in deals}
    assert "techmikeny" in sources
    assert "ebay" in sources


async def test_search_item_without_shopify_adapters_is_ebay_only(db):
    """Default poller (no Shopify adapters configured) behaves exactly as before."""
    item = await _add_item(db)
    poller = EbayPoller()
    poller.shopify_adapters = []  # explicitly none
    poller.client = _StubEbayClient([_raw_ebay("e1", "300")])

    result = await poller.search_item(db, item)
    await db.flush()
    listings = (await db.execute(select(Listing).where(Listing.tracked_item_id == item.id))).scalars().all()
    assert {ll.source for ll in listings} == {"ebay"}
    assert result["new_listings"] == 1
