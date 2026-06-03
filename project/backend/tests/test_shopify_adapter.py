"""story-E: generic ShopifyJsonLdAdapter (/products.json + schema.org JSON-LD).

Data-driven per-source config (TechMikeNY -> UnixSurplus -> ServerMonkey), with a
mockable transport (NEVER a live call in tests). Emits NormalizedListing rows
keyed by (source, source_listing_id=variant id) so they dedup against the eBay
feed (TechMikeNY appears in both). Own per-source rate bucket.
"""
from app.models.tracked_item import TrackedItem
from app.services.sources.base import NormalizedListing, SourceAdapter
from app.services.sources.shopify import ShopifyJsonLdAdapter, ShopifySourceConfig


class _FakeShopTransport:
    """Returns a canned /products.json payload; records the fetched URL."""

    def __init__(self, payload: dict):
        self._payload = payload
        self.urls = []

    async def fetch_products_json(self, base_url: str, query: str, page: int = 1) -> dict:
        self.urls.append((base_url, query, page))
        return self._payload


_PRODUCTS_JSON = {
    "products": [
        {
            "id": 111,
            "title": "Dell PowerEdge R740 EPYC Server",
            "handle": "r740-epyc",
            "vendor": "TechMikeNY",
            "variants": [
                {"id": 9001, "title": "Default", "price": "1499.00", "available": True},
                {"id": 9002, "title": "Upgraded", "price": "1899.00", "available": False},
            ],
        },
        {
            "id": 222,
            "title": "Unrelated Keyboard",
            "handle": "keyboard",
            "vendor": "TechMikeNY",
            "variants": [{"id": 9100, "title": "Default", "price": "29.00", "available": True}],
        },
    ]
}


def _techmikeny() -> ShopifySourceConfig:
    return ShopifySourceConfig(source="techmikeny", base_url="https://techmikeny.com", merchant="TechMikeNY")


async def _add_item(db, keywords="PowerEdge R740") -> TrackedItem:
    item = TrackedItem(id=42, name="R740", keywords=keywords, is_enabled=True)
    db.add(item)
    await db.flush()
    return item


def test_shopify_adapter_is_a_source_adapter():
    adapter = ShopifyJsonLdAdapter(_techmikeny(), transport=_FakeShopTransport(_PRODUCTS_JSON))
    assert isinstance(adapter, SourceAdapter)
    assert adapter.source == "techmikeny"


async def test_parses_products_json_into_normalized_listings(db):
    item = await _add_item(db, keywords="PowerEdge R740")
    transport = _FakeShopTransport(_PRODUCTS_JSON)
    adapter = ShopifyJsonLdAdapter(_techmikeny(), transport=transport, enabled=True)

    out = await adapter.search(item)

    # Only available variants of the keyword-matching product become listings.
    assert all(isinstance(x, NormalizedListing) for x in out)
    ids = {nl.source_listing_id for nl in out}
    assert "9001" in ids          # available, matches "PowerEdge R740"
    assert "9002" not in ids      # not available
    assert "9100" not in ids      # keyword mismatch (keyboard)

    nl = next(nl for nl in out if nl.source_listing_id == "9001")
    assert nl.source == "techmikeny"
    assert nl.price == 1499.00
    assert nl.currency == "USD"
    assert nl.seller == "TechMikeNY"
    assert nl.condition == "Used"
    assert nl.url == "https://techmikeny.com/products/r740-epyc?variant=9001"
    assert nl.catalog_item_id == 42


async def test_disabled_returns_empty(db):
    item = await _add_item(db)
    transport = _FakeShopTransport(_PRODUCTS_JSON)
    adapter = ShopifyJsonLdAdapter(_techmikeny(), transport=transport, enabled=False)
    assert await adapter.search(item) == []
    assert transport.urls == []


async def test_rate_bucket_blocks_after_limit(db):
    item = await _add_item(db)
    transport = _FakeShopTransport(_PRODUCTS_JSON)
    adapter = ShopifyJsonLdAdapter(_techmikeny(), transport=transport, enabled=True, daily_limit=1)

    first = await adapter.search(item)
    assert first  # got listings
    second = await adapter.search(item)
    assert second == []  # bucket exhausted -> no fetch
    assert len(transport.urls) == 1


async def test_config_is_per_source_data_driven(db):
    # The SAME adapter class serves a different retailer purely via config.
    item = await _add_item(db)
    cfg = ShopifySourceConfig(source="unixsurplus", base_url="https://unixsurplus.com", merchant="UNIXSurplus")
    adapter = ShopifyJsonLdAdapter(cfg, transport=_FakeShopTransport(_PRODUCTS_JSON), enabled=True)

    out = await adapter.search(item)
    assert adapter.source == "unixsurplus"
    assert any(nl.url.startswith("https://unixsurplus.com/products/") for nl in out)
    assert all(nl.seller == "UNIXSurplus" for nl in out)
