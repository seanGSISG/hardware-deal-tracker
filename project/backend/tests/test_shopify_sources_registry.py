"""story-1 / story-2: per-source Shopify registry + robots/ToS gating + fixtures.

Each onboarded Shopify retailer has a ShopifySourceConfig plus a recorded
robots.txt/ToS verification that GATES enablement. The registry builds adapters
ONLY for sources that are (a) globally enabled, (b) per-store enabled, and
(c) robots/ToS-verified. A failing/absent verification keeps the source dark even
when ENABLE_SHOPIFY_SOURCES is true. Mock-transport parse/poll tests run against
captured /products.json fixtures and NEVER hit a live store.
"""
from app.models.tracked_item import TrackedItem
from app.services.sources.base import NormalizedListing
from app.services.sources.shopify import ShopifyJsonLdAdapter
from app.services.sources.shopify_sources import (
    PRIMARY_SOURCES,
    SECONDARY_SOURCES,
    SHOPIFY_SOURCES,
    build_shopify_adapters,
)
from tests.fixtures import load_products_json


class _FixtureTransport:
    """Returns a captured /products.json fixture; records fetched URLs."""

    def __init__(self, payload: dict):
        self._payload = payload
        self.urls: list = []

    async def fetch_products_json(self, base_url: str, query: str, page: int = 1) -> dict:
        self.urls.append((base_url, query, page))
        return self._payload


# Keyword per fixture so the adapter's keyword filter matches exactly one product.
_KEYWORDS = {
    "techmikeny": "H12SSL-CT",
    "unixsurplus": "ConnectX-5 MCX512A",
    "servermonkey": "P5510 1.92TB",
    "cloud_ninjas": "PM9A3 1.92TB",
    "natex": "M393A8G40AB2-CWE",
    "savemyserver": "Exos X16 16TB",
}

_EXPECTED_VARIANT = {
    "techmikeny": "41000001",
    "unixsurplus": "52000001",
    "servermonkey": "63000001",
    "cloud_ninjas": "14000001",
    "natex": "15000001",
    "savemyserver": "16000001",
}


async def _add_item(db, keywords: str) -> TrackedItem:
    item = TrackedItem(name="x", keywords=keywords, is_enabled=True)
    db.add(item)
    await db.flush()
    return item


def test_registry_has_all_six_onboarded_sources():
    assert set(PRIMARY_SOURCES) == {"techmikeny", "unixsurplus", "servermonkey"}
    assert set(SECONDARY_SOURCES) == {"cloud_ninjas", "natex", "savemyserver"}
    for src in PRIMARY_SOURCES + SECONDARY_SOURCES:
        entry = SHOPIFY_SOURCES[src]
        assert entry.config.source == src
        assert entry.config.base_url.startswith("https://")
        assert entry.config.currency == "USD"
        assert entry.config.merchant


def test_every_source_carries_a_robots_tos_verification():
    for _src, entry in SHOPIFY_SOURCES.items():
        v = entry.verification
        assert v.platform == "Shopify"
        assert v.products_json_url.endswith("/products.json")
        assert v.tos_checked_on  # ISO date string
        assert isinstance(v.robots_allows_products_json, bool)


def test_savemyserver_is_low_cadence_memory_signal():
    # SaveMyServer is a price-MEMORY source: a smaller daily limit than primaries.
    sms = SHOPIFY_SOURCES["savemyserver"]
    tmn = SHOPIFY_SOURCES["techmikeny"]
    assert sms.daily_limit < tmn.daily_limit
    assert sms.is_price_memory is True


def test_build_adapters_respects_global_disable():
    adapters = build_shopify_adapters(
        transport=_FixtureTransport({"products": []}),
        global_enabled=False,
    )
    assert adapters == []


def test_build_adapters_skips_unverified_source():
    # Force one source's verification to fail -> it must not be built even when
    # globally + per-store enabled.
    adapters = build_shopify_adapters(
        transport=_FixtureTransport({"products": []}),
        global_enabled=True,
        per_store_enabled=dict.fromkeys(SHOPIFY_SOURCES, True),
        verification_overrides={"techmikeny": False},
    )
    built = {a.source for a in adapters}
    assert "techmikeny" not in built
    # Other verified+enabled sources are still built.
    assert "unixsurplus" in built


def test_build_adapters_skips_per_store_disabled():
    adapters = build_shopify_adapters(
        transport=_FixtureTransport({"products": []}),
        global_enabled=True,
        per_store_enabled={s: (s != "natex") for s in SHOPIFY_SOURCES},
    )
    built = {a.source for a in adapters}
    assert "natex" not in built
    assert "techmikeny" in built


def test_built_adapters_get_isolated_buckets():
    transport = _FixtureTransport({"products": []})
    adapters = build_shopify_adapters(
        transport=transport,
        global_enabled=True,
        per_store_enabled=dict.fromkeys(SHOPIFY_SOURCES, True),
    )
    # Each adapter has its own daily limit from its registry entry.
    by_source = {a.source: a for a in adapters}
    assert by_source["savemyserver"].budget.status("savemyserver")["daily_limit"] == (
        SHOPIFY_SOURCES["savemyserver"].daily_limit
    )
    # Buckets are independent: exhausting one does not touch another.
    smb = by_source["savemyserver"].budget
    for _ in range(SHOPIFY_SOURCES["savemyserver"].daily_limit):
        smb.record_call("savemyserver")
    assert smb.can_call("savemyserver") is False


# -- Per-site mock-transport parse/poll tests against captured fixtures --------

async def _assert_site_normalizes(db, source: str):
    item = await _add_item(db, _KEYWORDS[source])
    entry = SHOPIFY_SOURCES[source]
    transport = _FixtureTransport(load_products_json(source))
    adapter = ShopifyJsonLdAdapter(
        entry.config, transport=transport, enabled=True, daily_limit=entry.daily_limit
    )

    out = await adapter.search(item)

    assert out, f"{source}: expected at least one normalized listing"
    assert all(isinstance(x, NormalizedListing) for x in out)
    ids = {nl.source_listing_id for nl in out}
    assert _EXPECTED_VARIANT[source] in ids
    nl = next(nl for nl in out if nl.source_listing_id == _EXPECTED_VARIANT[source])
    assert nl.source == source
    assert nl.currency == "USD"
    assert nl.seller == entry.config.merchant
    assert nl.price > 0
    # price+shipping total is exposed for scoring/comparison.
    assert nl.total == nl.price + nl.shipping
    assert nl.url.startswith(entry.config.base_url)
    assert nl.catalog_item_id == item.id
    assert transport.urls, "transport should have been called for an enabled+verified source"


async def test_techmikeny_fixture_normalizes(db):
    await _assert_site_normalizes(db, "techmikeny")


async def test_unixsurplus_fixture_normalizes(db):
    await _assert_site_normalizes(db, "unixsurplus")


async def test_servermonkey_fixture_normalizes(db):
    await _assert_site_normalizes(db, "servermonkey")


async def test_cloud_ninjas_fixture_normalizes(db):
    await _assert_site_normalizes(db, "cloud_ninjas")


async def test_natex_fixture_normalizes(db):
    await _assert_site_normalizes(db, "natex")


async def test_savemyserver_fixture_normalizes(db):
    await _assert_site_normalizes(db, "savemyserver")
