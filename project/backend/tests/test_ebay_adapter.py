"""story-B: EbayBrowseAdapter — eBay as the first SourceAdapter.

Refactors the existing eBay client+parser into the SourceAdapter contract
without regressing the poller. The adapter emits NormalizedListing rows with
source="ebay" and source_listing_id=itemId.
"""
from app.models.tracked_item import TrackedItem
from app.services.sources.base import NormalizedListing, SourceAdapter
from app.services.sources.ebay import EbayBrowseAdapter


class _StubClient:
    def __init__(self, items):
        self._items = items
        self.calls = []

    async def search(self, keywords, **kwargs):
        self.calls.append((keywords, kwargs))
        return {"itemSummaries": self._items, "total": len(self._items), "offset": 0, "limit": 200}


def _raw_item(item_id: str, price: str, shipping: str = "0") -> dict:
    return {
        "itemId": item_id,
        "title": f"Test {item_id}",
        "price": {"value": price, "currency": "USD"},
        "shippingOptions": [{"shippingCost": {"value": shipping, "currency": "USD"}}],
        "seller": {"username": "seller", "feedbackScore": 500, "feedbackPercentage": "99.0"},
        "condition": "Used",
        "conditionId": "3000",
        "itemWebUrl": f"https://www.ebay.com/itm/{item_id}",
        "buyingOptions": ["FIXED_PRICE"],
    }


def test_ebay_adapter_is_a_source_adapter():
    adapter = EbayBrowseAdapter()
    assert isinstance(adapter, SourceAdapter)
    assert adapter.source == "ebay"


async def test_ebay_adapter_search_returns_normalized_listings():
    adapter = EbayBrowseAdapter()
    adapter.client = _StubClient([_raw_item("v1|111|0", "300", "9.99")])

    item = TrackedItem(id=3, name="EPYC 7F72", keywords="EPYC 7F72", category_id="164")
    out = await adapter.search(item)

    assert len(out) == 1
    nl = out[0]
    assert isinstance(nl, NormalizedListing)
    assert nl.source == "ebay"
    assert nl.source_listing_id == "v1|111|0"
    assert nl.price == 300.0
    assert nl.shipping == 9.99
    assert nl.total == 309.99
    assert nl.catalog_item_id == 3
    assert nl.seller == "seller"
    assert nl.condition == "Used"
    assert nl.url == "https://www.ebay.com/itm/v1|111|0"
    # raw_payload preserves the original eBay item dict for downstream parsing.
    assert nl.raw_payload["itemId"] == "v1|111|0"


async def test_ebay_adapter_passes_keywords_and_category_to_client():
    adapter = EbayBrowseAdapter()
    stub = _StubClient([])
    adapter.client = stub

    item = TrackedItem(id=1, name="x", keywords="connectx-6", category_id="175709")
    await adapter.search(item)

    keywords, kwargs = stub.calls[0]
    assert keywords == "connectx-6"
    assert kwargs.get("category_id") == "175709"
