"""story-D: PcPartPickerAdapter — BENCHMARK-only source (never scored/deduped).

Reuses the pypartpicker data-model concept (Part / Vendor / Price) but with our
own injected transport (NEVER a live network call in tests). It refreshes a
catalog item's benchmark_median plus a 'vs retail' delta. It is gated behind
ENABLE_PCPARTPICKER (default OFF), uses its own rate bucket (<=200/day, separate
from eBay), and trips a circuit breaker after repeated transport errors.
"""
import pytest

from app.models.tracked_item import TrackedItem
from app.services.sources.pcpartpicker import (
    PcPartPickerAdapter,
    PcppPart,
    PcppPrice,
    PcppVendor,
)


class _FakeTransport:
    """Injected transport stand-in: returns canned Part payloads, no network."""

    def __init__(self, parts: dict, raise_exc: Exception | None = None):
        self._parts = parts
        self._raise = raise_exc
        self.calls = []

    async def fetch_part(self, product_id: str, region: str = "us"):
        self.calls.append(product_id)
        if self._raise is not None:
            raise self._raise
        return self._parts[product_id]


def _part(product_id: str, vendor_totals: list[float]) -> PcppPart:
    vendors = [
        PcppVendor(
            name=f"vendor{i}",
            in_stock=True,
            price=PcppPrice(base=total, shipping=0.0, total=total, currency="USD"),
        )
        for i, total in enumerate(vendor_totals)
    ]
    return PcppPart(
        product_id=product_id,
        name=f"Part {product_id}",
        type="video-card",
        url=f"https://pcpartpicker.com/product/{product_id}/",
        vendors=vendors,
    )


async def _add_mappable_item(db, pcpp_product_id="abc123", benchmark_median=900) -> TrackedItem:
    item = TrackedItem(
        name="RTX 6000 Ada",
        keywords="RTX 6000 Ada",
        benchmark_median=benchmark_median,
        pcpp_product_id=pcpp_product_id,
        is_enabled=True,
    )
    db.add(item)
    await db.flush()
    return item


def test_part_cheapest_total_picks_lowest_instock_vendor():
    part = _part("abc123", [1200.0, 950.0, 1050.0])
    assert part.cheapest_total() == 950.0


def test_part_cheapest_ignores_out_of_stock():
    part = _part("abc123", [1200.0])
    part.vendors.append(
        PcppVendor(name="oos", in_stock=False, price=PcppPrice(base=10, shipping=0, total=10, currency="USD"))
    )
    assert part.cheapest_total() == 1200.0


async def test_disabled_by_default_does_nothing(db):
    item = await _add_mappable_item(db, benchmark_median=900)
    transport = _FakeTransport({"abc123": _part("abc123", [800.0])})
    adapter = PcPartPickerAdapter(transport=transport, enabled=False)

    result = await adapter.refresh_benchmark(item)

    assert result["skipped"] is True
    assert transport.calls == []  # never even fetched
    assert float(item.benchmark_median) == 900  # unchanged


async def test_refresh_updates_benchmark_and_vs_retail_delta(db):
    item = await _add_mappable_item(db, benchmark_median=900)
    transport = _FakeTransport({"abc123": _part("abc123", [1000.0, 800.0])})
    adapter = PcPartPickerAdapter(transport=transport, enabled=True)

    result = await adapter.refresh_benchmark(item)

    # Cheapest new-retail total becomes the new benchmark_median.
    assert float(item.benchmark_median) == 800.0
    assert result["benchmark_median"] == 800.0
    assert result["condition"] == "new"
    # vs-retail delta vs the previous benchmark (900 -> 800).
    assert result["vs_retail_delta"] == pytest.approx(-100.0)


async def test_item_without_pcpp_id_is_skipped(db):
    item = await _add_mappable_item(db, pcpp_product_id=None)
    transport = _FakeTransport({})
    adapter = PcPartPickerAdapter(transport=transport, enabled=True)

    result = await adapter.refresh_benchmark(item)
    assert result["skipped"] is True
    assert transport.calls == []


async def test_rate_bucket_blocks_after_limit(db):
    item = await _add_mappable_item(db)
    transport = _FakeTransport({"abc123": _part("abc123", [800.0])})
    adapter = PcPartPickerAdapter(transport=transport, enabled=True, daily_limit=1)

    first = await adapter.refresh_benchmark(item)
    assert first.get("skipped") is not True

    second = await adapter.refresh_benchmark(item)
    assert second["skipped"] is True
    assert second["reason"] == "rate_budget_exhausted"


async def test_circuit_breaker_opens_after_repeated_errors(db):
    item = await _add_mappable_item(db)
    transport = _FakeTransport({}, raise_exc=RuntimeError("cloudflare 403"))
    adapter = PcPartPickerAdapter(transport=transport, enabled=True, breaker_threshold=2)

    r1 = await adapter.refresh_benchmark(item)
    assert r1["error"]
    r2 = await adapter.refresh_benchmark(item)
    assert r2["error"]
    # Breaker now open -> no further transport calls.
    calls_before = len(transport.calls)
    r3 = await adapter.refresh_benchmark(item)
    assert r3["skipped"] is True
    assert r3["reason"] == "circuit_open"
    assert len(transport.calls) == calls_before


async def test_search_returns_empty_not_routed_to_pipeline(db):
    # Benchmark-only: search() (the SourceAdapter contract) yields NO listings,
    # so PCPartPicker rows never enter the eBay scoring/dedup/notification path.
    item = await _add_mappable_item(db)
    transport = _FakeTransport({"abc123": _part("abc123", [800.0])})
    adapter = PcPartPickerAdapter(transport=transport, enabled=True)
    assert await adapter.search(item) == []
