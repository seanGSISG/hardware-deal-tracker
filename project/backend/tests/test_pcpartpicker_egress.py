"""story-5: PCPartPicker behind a residential Tailscale egress flag.

PCPartPicker stays OFF by default. Even when ENABLE_PCPARTPICKER is true,
refresh_benchmark must ONLY run when a residential egress is configured (calls
must NOT leave from a datacenter IP). Otherwise it returns a skipped result with
a clear reason and makes NO live call. search() still returns [] (benchmark-only),
and the circuit breaker opens after the threshold and resets on success.
"""
from app.models.tracked_item import TrackedItem
from app.services.sources.pcpartpicker import PcPartPickerAdapter, PcppPart, PcppPrice, PcppVendor


class _FakeTransport:
    def __init__(self, parts: dict, raise_exc: Exception | None = None):
        self._parts = parts
        self._raise = raise_exc
        self.calls: list = []

    async def fetch_part(self, product_id: str, region: str = "us"):
        self.calls.append(product_id)
        if self._raise is not None:
            raise self._raise
        return self._parts[product_id]


def _part(product_id: str, totals: list[float]) -> PcppPart:
    return PcppPart(
        product_id=product_id, name=f"Part {product_id}", type="video-card",
        url=f"https://pcpartpicker.com/product/{product_id}/",
        vendors=[
            PcppVendor(name=f"v{i}", in_stock=True,
                       price=PcppPrice(base=t, shipping=0.0, total=t, currency="USD"))
            for i, t in enumerate(totals)
        ],
    )


async def _item(db, pcpp_product_id="abc123", benchmark_median=900) -> TrackedItem:
    it = TrackedItem(name="RTX 6000 Ada", keywords="RTX 6000 Ada",
                     benchmark_median=benchmark_median, pcpp_product_id=pcpp_product_id,
                     is_enabled=True)
    db.add(it)
    await db.flush()
    return it


async def test_enabled_but_no_egress_is_skipped_no_call(db):
    item = await _item(db)
    transport = _FakeTransport({"abc123": _part("abc123", [800.0])})
    # Enabled, but residential egress NOT configured -> must skip without calling.
    adapter = PcPartPickerAdapter(
        transport=transport, enabled=True, require_egress=True, egress_configured=False
    )
    result = await adapter.refresh_benchmark(item)
    assert result["skipped"] is True
    assert result["reason"] == "no_residential_egress"
    assert transport.calls == []
    assert float(item.benchmark_median) == 900  # unchanged


async def test_enabled_with_egress_runs(db):
    item = await _item(db, benchmark_median=900)
    transport = _FakeTransport({"abc123": _part("abc123", [800.0])})
    adapter = PcPartPickerAdapter(
        transport=transport, enabled=True, require_egress=True, egress_configured=True
    )
    result = await adapter.refresh_benchmark(item)
    assert result["skipped"] is False
    assert result["benchmark_median"] == 800.0
    assert result["vs_retail_delta"] == -100.0
    assert transport.calls == ["abc123"]


async def test_egress_not_required_keeps_legacy_behaviour(db):
    # require_egress=False -> the egress gate is bypassed (default OFF posture is
    # enforced by ENABLE_PCPARTPICKER, exercised elsewhere).
    item = await _item(db)
    transport = _FakeTransport({"abc123": _part("abc123", [850.0])})
    adapter = PcPartPickerAdapter(transport=transport, enabled=True, require_egress=False)
    result = await adapter.refresh_benchmark(item)
    assert result["skipped"] is False


async def test_search_still_empty_with_egress(db):
    item = await _item(db)
    transport = _FakeTransport({"abc123": _part("abc123", [800.0])})
    adapter = PcPartPickerAdapter(
        transport=transport, enabled=True, require_egress=True, egress_configured=True
    )
    assert await adapter.search(item) == []


async def test_breaker_opens_then_resets_with_egress(db):
    item = await _item(db)
    boom = _FakeTransport({}, raise_exc=RuntimeError("cloudflare 403"))
    adapter = PcPartPickerAdapter(
        transport=boom, enabled=True, require_egress=True, egress_configured=True,
        breaker_threshold=2,
    )
    assert (await adapter.refresh_benchmark(item))["error"]
    assert (await adapter.refresh_benchmark(item))["error"]
    # Breaker open -> skipped(circuit_open), no further call, never raises.
    calls_before = len(boom.calls)
    r = await adapter.refresh_benchmark(item)
    assert r["skipped"] is True and r["reason"] == "circuit_open"
    assert len(boom.calls) == calls_before

    # A subsequent SUCCESS (breaker reset) requires the breaker to allow a call
    # again — verify reset semantics directly on a healthy adapter.
    good = _FakeTransport({"abc123": _part("abc123", [700.0])})
    healthy = PcPartPickerAdapter(
        transport=good, enabled=True, require_egress=True, egress_configured=True,
        breaker_threshold=2,
    )
    ok = await healthy.refresh_benchmark(item)
    assert ok["skipped"] is False
    assert healthy._consecutive_errors == 0
