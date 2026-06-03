"""PcPartPickerAdapter — BENCHMARK-only price reference (feature-005, story-D).

Design notes (see plan/MVP2_PCPARTPICKER_RESEARCH.md):
- PCPartPicker is a *reference/benchmark* source ONLY. It refreshes a catalog
  item's `benchmark_median` (cheapest in-stock new-retail total) plus a
  'vs retail' delta. Its rows are NEVER routed through the eBay scoring / dedup /
  notification pipeline; condition is always "new". Accordingly `search()` (the
  SourceAdapter contract) returns an EMPTY list so the poller never ingests it.
- We reuse the `lucwl/pypartpicker` DATA MODEL concept (Part / Vendor / Price)
  but with our OWN injected transport (mockable; the real one would be a
  TLS-impersonating `curl_cffi` fetcher behind a flag). Tests NEVER hit the live
  site — a transport is always injected.
- Gated behind `ENABLE_PCPARTPICKER` (default OFF), its own daily rate bucket
  (<=200/day, separate from eBay's 5000), and a circuit breaker that opens after
  repeated transport errors (Cloudflare blocks).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

from app.core.config import settings
from app.services.sources.base import NormalizedListing, SourceAdapter
from app.services.sources.rate_budget import SourceRateBudget

SOURCE = "pcpartpicker"


@dataclass
class PcppPrice:
    """A single vendor price (mirrors pypartpicker's Price)."""

    base: float
    shipping: float
    total: float
    currency: str = "USD"


@dataclass
class PcppVendor:
    """A vendor offer for a part (mirrors pypartpicker's Vendor)."""

    name: str
    in_stock: bool
    price: PcppPrice


@dataclass
class PcppPart:
    """A PCPartPicker product (subset of pypartpicker's Part)."""

    product_id: str
    name: str
    type: str
    url: str
    vendors: list[PcppVendor] = field(default_factory=list)
    specs: dict = field(default_factory=dict)

    def cheapest_total(self) -> float | None:
        """Cheapest in-stock vendor total (the new-retail benchmark)."""
        totals = [v.price.total for v in self.vendors if v.in_stock]
        return min(totals) if totals else None


class PcppTransport(Protocol):
    """Injected transport contract — implementations fetch a Part by id."""

    async def fetch_part(self, product_id: str, region: str = "us") -> PcppPart: ...


class PcPartPickerAdapter(SourceAdapter):
    """Benchmark-only PCPartPicker adapter (never enters the scoring pipeline)."""

    source = SOURCE

    def __init__(
        self,
        transport: PcppTransport,
        enabled: bool | None = None,
        daily_limit: int | None = None,
        breaker_threshold: int | None = None,
        region: str | None = None,
        budget: SourceRateBudget | None = None,
        require_egress: bool | None = None,
        egress_configured: bool | None = None,
    ):
        self.transport = transport
        self.enabled = settings.ENABLE_PCPARTPICKER if enabled is None else enabled
        self.region = region or settings.PCPARTPICKER_REGION
        # Residential Tailscale egress gate (feature-003, story-5). PCPartPicker
        # calls must leave from a RESIDENTIAL exit node, never a datacenter IP
        # (ToS + Cloudflare anti-bot). When `require_egress` is on, refresh only
        # runs if a residential egress is configured.
        self.require_egress = (
            settings.PCPARTPICKER_USE_RESIDENTIAL_EGRESS if require_egress is None else require_egress
        )
        if egress_configured is None:
            egress_configured = bool(settings.PCPARTPICKER_TAILSCALE_EXIT_NODE)
        self.egress_configured = egress_configured
        self._breaker_threshold = (
            settings.PCPARTPICKER_CIRCUIT_BREAKER_THRESHOLD if breaker_threshold is None else breaker_threshold
        )
        limit = settings.PCPARTPICKER_DAILY_LIMIT if daily_limit is None else daily_limit
        self.budget = budget or SourceRateBudget()
        self.budget.configure(self.source, daily_limit=limit)
        self._consecutive_errors = 0
        self._breaker_open = False

    async def search(self, catalog_item) -> list[NormalizedListing]:
        # Benchmark-only: deliberately yields nothing to the poller pipeline.
        return []

    async def refresh_benchmark(self, catalog_item) -> dict:
        """Refresh `benchmark_median` + 'vs retail' delta for a mappable item."""
        if not self.enabled:
            return {"skipped": True, "reason": "disabled"}
        # Residential egress gate: never call PCPartPicker from a datacenter IP.
        if self.require_egress and not self.egress_configured:
            return {"skipped": True, "reason": "no_residential_egress"}
        if not getattr(catalog_item, "pcpp_product_id", None):
            return {"skipped": True, "reason": "no_pcpp_product_id"}
        if self._breaker_open:
            return {"skipped": True, "reason": "circuit_open"}
        if not self.budget.can_call(self.source):
            return {"skipped": True, "reason": "rate_budget_exhausted"}

        self.budget.record_call(self.source)
        try:
            part = await self.transport.fetch_part(catalog_item.pcpp_product_id, region=self.region)
        except Exception as exc:  # noqa: BLE001 — record, trip breaker, never raise
            self._consecutive_errors += 1
            if self._consecutive_errors >= self._breaker_threshold:
                self._breaker_open = True
            return {"skipped": True, "error": str(exc), "circuit_open": self._breaker_open}

        # Success resets the breaker.
        self._consecutive_errors = 0

        cheapest = part.cheapest_total()
        if cheapest is None:
            return {"skipped": True, "reason": "no_in_stock_vendor"}

        previous = float(catalog_item.benchmark_median) if catalog_item.benchmark_median is not None else None
        catalog_item.benchmark_median = cheapest
        vs_retail_delta = round(cheapest - previous, 2) if previous is not None else None

        return {
            "skipped": False,
            "source": self.source,
            "pcpp_product_id": catalog_item.pcpp_product_id,
            "benchmark_median": cheapest,
            "previous_benchmark": previous,
            "vs_retail_delta": vs_retail_delta,
            "condition": "new",
        }
