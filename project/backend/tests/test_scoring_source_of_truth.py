"""T3.2 — the scoring engine derives its benchmark solely from the passed
catalog item / historical stats. The drifting in-module BENCHMARK_PRICES dict
(and its get_benchmark_price lookup) must be gone, so the catalog is the single
source of truth for benchmark prices.
"""
from decimal import Decimal

from app.services.scoring.engine import DealScoringEngine


class _Listing:
    """Minimal stand-in for a Listing row (engine only reads these attrs)."""

    def __init__(self, price, shipping=0.0, title="Test item", condition="used"):
        self.price = Decimal(str(price))
        self.shipping = Decimal(str(shipping))
        self.title = title
        self.condition = condition
        self.seller_feedback = 500
        self.seller_positive_pct = Decimal("99.0")
        self.quantity = 1


class _CatalogItem:
    def __init__(self, benchmark_median, scam_floor=0.0):
        self.benchmark_median = benchmark_median
        self.scam_floor = scam_floor


def test_benchmark_prices_dict_and_lookup_are_removed():
    """The dead, drift-prone benchmark dict + lookup helper no longer exist."""
    assert not hasattr(DealScoringEngine, "BENCHMARK_PRICES")
    assert not hasattr(DealScoringEngine, "get_benchmark_price")


def test_benchmark_derives_from_catalog_item_when_no_history():
    """With no historical median, the engine falls back to catalog_item.benchmark_median."""
    engine = DealScoringEngine()
    listing = _Listing(price=200.0)
    catalog_item = _CatalogItem(benchmark_median=400.0)

    result = engine.calculate_overall_score(listing, {}, catalog_item=catalog_item)

    # est_fair_value should reflect the catalog benchmark, not the listing price.
    assert result["est_fair_value"] == 400.0
    # 50% under benchmark => a strong deal.
    assert result["overall_score"] >= 70


def test_historical_median_takes_precedence_over_catalog():
    """When history is present, it wins; the catalog is only a fallback."""
    engine = DealScoringEngine()
    listing = _Listing(price=200.0)
    catalog_item = _CatalogItem(benchmark_median=400.0)

    stats = {"median_price": 600.0, "avg_price": 600.0, "std_dev": 50.0, "data_points": 30}
    result = engine.calculate_overall_score(listing, stats, catalog_item=catalog_item)

    assert result["est_fair_value"] == 600.0


def test_no_catalog_no_history_does_not_crash():
    """Empty-DB safety: scoring a listing with neither history nor catalog item is graceful."""
    engine = DealScoringEngine()
    listing = _Listing(price=200.0)

    result = engine.calculate_overall_score(listing, {}, catalog_item=None)

    assert 0 <= result["overall_score"] <= 100
    assert result["est_fair_value"] == 200.0
