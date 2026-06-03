"""T3.6 — HardwareCatalog integrity checks.

Kept deliberately tolerant on the exact item count and on seed-parity (feature-004
owns generate_seed.py and may regenerate the seed): we assert structural invariants
the scoring pipeline relies on, not brittle exact values.
"""
from app.services.ebay.catalog import CatalogItem, HardwareCatalog


def test_catalog_is_non_empty():
    assert len(HardwareCatalog.ITEMS) >= 1


def test_every_item_has_required_fields():
    for item in HardwareCatalog.ITEMS:
        assert isinstance(item, CatalogItem)
        assert item.name and item.name.strip()
        assert item.keywords and item.keywords.strip()
        # scam_floor and benchmark_median drive scoring + scam detection.
        assert item.scam_floor is not None
        assert item.benchmark_median is not None
        assert item.scam_floor >= 0
        assert item.benchmark_median > 0


def test_scam_floor_below_benchmark_median():
    # A scam floor at/above the benchmark would flag legit listings as scams.
    for item in HardwareCatalog.ITEMS:
        assert item.scam_floor <= item.benchmark_median, item.name


def test_item_names_are_unique():
    names = [item.name for item in HardwareCatalog.ITEMS]
    assert len(names) == len(set(names))


def test_search_intervals_are_positive():
    for item in HardwareCatalog.ITEMS:
        assert item.search_interval > 0
