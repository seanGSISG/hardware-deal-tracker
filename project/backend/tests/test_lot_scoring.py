"""Lot (multi-module) handling: the parser reads a lot size from the title and
the scoring engine judges the listing on its per-stick price, so a good 4x/8x
lot surfaces as a deal instead of being penalised by its lot total.
"""
from decimal import Decimal

import pytest

from app.services.ebay.parser import detect_lot_size
from app.services.scoring.engine import DealScoringEngine


class _Listing:
    def __init__(self, price, quantity=1, shipping=0.0, title="Test item", condition="used"):
        self.price = Decimal(str(price))
        self.shipping = Decimal(str(shipping))
        self.title = title
        self.condition = condition
        self.seller_feedback = 500
        self.seller_positive_pct = Decimal("99.0")
        self.quantity = quantity


class _CatalogItem:
    def __init__(self, benchmark_median, scam_floor=0.0):
        self.benchmark_median = benchmark_median
        self.scam_floor = scam_floor


@pytest.mark.parametrize(
    "title,expected",
    [
        ("Micron 32GB DDR4-3200 ECC RDIMM MTA18ASF4G72PZ-3G2F1UI", 1),
        ("Lot of 8 Micron 32GB DDR4-3200 ECC RDIMM Server Memory", 8),
        ("8x Micron 32GB DDR4-3200 RDIMM REG ECC", 8),
        ("Hynix 64GB (4 x 64GB) DDR4-3200 ECC RDIMM", 4),
        ("Kingston KSM32RD4/32MEI 32GB DDR4-3200 ECC qty 4", 4),
        # Rank notation must NOT be read as a lot:
        ("Samsung 64GB 2Rx4 PC4-3200AA RDIMM M393A8G40AB2-CWE", 1),
        ("SK Hynix 64GB 4Rx4 PC4-25600L LRDIMM", 1),
        # Ambiguous "pick your quantity" listings fall back to single:
        ("2x 4x 8x Micron 32GB 3200MHz DDR4-3200 Server Memory RDIMM", 1),
        ("", 1),
        # PCIe lane width is NOT a lot size. These used to parse as x16/x8 lots,
        # which divided the price by the lane count, tripped scam_floor, and
        # muted the alert for every GPU/NIC/HBA listing (found live on the Arc
        # Pro B70 watch, 2026-08-26).
        ("GUNNIR Intel Arc Pro B70 TF Dual-Slot 32GB GDDR6 PCIe5.0 x16 2 Fan", 1),
        ("ASRock Arc Pro B70 Creator 32GB GDDR6 PCIe 5.0 x16", 1),
        ("NVIDIA RTX A5000 24GB PCI-E 4.0 x16 Workstation GPU", 1),
        ("Mellanox ConnectX-5 MCX516A PCIe Gen3 x8 100GbE", 1),
        ("Intel X710-DA4 10GbE SFP+ PCIe x8", 1),
        # Model names carrying an "X<n>" token are not lots either -- "Exos X16"
        # was reading as a lot of 16 on every Exos X16 listing in the table.
        ("Seagate Exos X16 16TB ST16000NM001G 3.5 SATA Enterprise HDD", 1),
        ("Seagate Exos 16TB X16 ST16000NM001G Factory Warranty Unopened", 1),
        # ...but real lots still count, including in those same titles:
        ("Lot of 4 NVIDIA T4 16GB PCIe 3.0 x16", 4),
        ("(Lot of 4) [Seagate Exos X16] 16TB, 7200RPM, SATA III, 3.5-inch", 4),
        ("2x 16TB Seagate Exos X16 7200RPM 3.5 SATA III Enterprise", 2),
        ("Pack of 7 x Seagate Exos X18 18TB 3.5 SATA III Enterprise HDDs", 7),
    ],
)
def test_detect_lot_size(title, expected):
    assert detect_lot_size(title) == expected


def test_lot_scored_on_per_unit_price_surfaces_as_deal():
    """An 8x lot at $1,200 total ($150/stick) vs a $250/stick benchmark is a
    strong deal — the engine must score it on $150, not $1,200."""
    engine = DealScoringEngine()
    catalog = _CatalogItem(benchmark_median=250.0)
    lot = _Listing(price=1200.0, quantity=8)

    result = engine.calculate_overall_score(lot, {}, catalog_item=catalog)

    assert result["overall_score"] >= 70


def test_same_lot_total_as_single_would_score_poorly():
    """Sanity contrast: if that $1,200 listing were a *single* module, it's far
    over the $250 benchmark and must NOT look like a deal."""
    engine = DealScoringEngine()
    catalog = _CatalogItem(benchmark_median=250.0)
    single = _Listing(price=1200.0, quantity=1)

    result = engine.calculate_overall_score(single, {}, catalog_item=catalog)

    assert result["overall_score"] < 50


def test_scam_floor_checked_per_unit():
    """A lot whose per-stick price falls below the scam floor is flagged, even
    though the lot total is well above it."""
    engine = DealScoringEngine()
    catalog = _CatalogItem(benchmark_median=250.0, scam_floor=140.0)
    lot = _Listing(price=880.0, quantity=8)  # $110/stick < $140 floor

    result = engine.calculate_overall_score(lot, {}, catalog_item=catalog)

    assert result["scam_warning"] is not None


def test_single_listing_behaviour_unchanged():
    """quantity==1 keeps the original semantics (regression guard)."""
    engine = DealScoringEngine()
    catalog = _CatalogItem(benchmark_median=400.0)
    single = _Listing(price=200.0, quantity=1)

    result = engine.calculate_overall_score(single, {}, catalog_item=catalog)

    assert result["est_fair_value"] == 400.0
    assert result["overall_score"] >= 70
