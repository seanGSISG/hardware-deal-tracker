"""story-A: SourceAdapter abstraction + NormalizedListing shape.

Defines the contract every ingestion source must implement so the poller can
fan out across sources without knowing their transport. The normalized shape is
the single record every adapter maps to (design_doc NormalizedListing).
"""
import inspect

import pytest

from app.models.tracked_item import TrackedItem
from app.services.sources.base import NormalizedListing, SourceAdapter


def test_normalized_listing_has_required_fields():
    nl = NormalizedListing(
        source="ebay",
        source_listing_id="v1|123|0",
        title="EPYC 7F72",
        url="https://www.ebay.com/itm/123",
        price=300.0,
        currency="USD",
        shipping=0.0,
        condition="Used",
        catalog_item_id=7,
        raw_payload={"itemId": "v1|123|0"},
    )
    assert nl.source == "ebay"
    assert nl.source_listing_id == "v1|123|0"
    assert nl.total == 300.0  # price + shipping convenience
    assert nl.availability is None
    assert nl.seller is None
    assert nl.fetched_at is not None  # auto-stamped


def test_total_includes_shipping():
    nl = NormalizedListing(
        source="ebay",
        source_listing_id="x",
        title="t",
        url="u",
        price=100.0,
        currency="USD",
        shipping=15.0,
        condition="New",
    )
    assert nl.total == 115.0


def test_source_adapter_is_abstract():
    # The base class declares an async search() and a source identity; it cannot
    # be instantiated directly (it is the conformance contract).
    with pytest.raises(TypeError):
        SourceAdapter()  # type: ignore[abstract]


def test_concrete_adapter_must_implement_search_and_source():
    class GoodAdapter(SourceAdapter):
        source = "good"

        async def search(self, catalog_item):
            return []

    adapter = GoodAdapter()
    assert adapter.source == "good"
    # search must be a coroutine function (async contract).
    assert inspect.iscoroutinefunction(adapter.search)


async def test_concrete_adapter_search_returns_normalized_listings():
    class OneAdapter(SourceAdapter):
        source = "one"

        async def search(self, catalog_item):
            return [
                NormalizedListing(
                    source=self.source,
                    source_listing_id="abc",
                    title=catalog_item.name,
                    url="https://example.com/abc",
                    price=42.0,
                    currency="USD",
                    shipping=0.0,
                    condition="New",
                    catalog_item_id=catalog_item.id,
                )
            ]

    item = TrackedItem(id=5, name="Widget", keywords="widget")
    out = await OneAdapter().search(item)
    assert len(out) == 1
    assert isinstance(out[0], NormalizedListing)
    assert out[0].source == "one"
    assert out[0].catalog_item_id == 5
