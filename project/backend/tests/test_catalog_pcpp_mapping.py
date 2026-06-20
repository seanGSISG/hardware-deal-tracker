"""story-4: pcpp_product_id mapping for the mappable catalog items.

The catalog items with a stable new-retail PCPartPicker product page (the
workstation GPUs + enterprise HDDs, ~8 after the 2026-06-20 EPYC-build rescope)
carry a non-null pcpp_product_id; enterprise/used-only SKUs stay null. The mapping must
round-trip from the catalog into TrackedItem.pcpp_product_id (column pre-exists,
no migration) and into the generated seed SQL.
"""
import importlib.util
from pathlib import Path

from sqlalchemy import select

from app.models.tracked_item import TrackedItem
from app.services.ebay.catalog import PCPP_MAPPINGS, HardwareCatalog

BACKEND_DIR = Path(__file__).resolve().parent.parent


def _mapped_items():
    return [i for i in HardwareCatalog.ITEMS if getattr(i, "pcpp_product_id", None)]


def test_catalog_item_has_pcpp_product_id_field():
    item = HardwareCatalog.ITEMS[0]
    assert hasattr(item, "pcpp_product_id")


def test_mapped_item_count_matches_scope():
    # 2 workstation GPUs (RTX PRO 6000, RTX PRO 4000) + 5 enterprise HDDs (MG08
    # stays unmapped) = 7 after the EPYC-build rescope + RTX 6000 Ada removal.
    mapped = _mapped_items()
    assert len(mapped) == 7, f"expected 7 mapped, got {len(mapped)}"


def test_mapped_ids_are_unique_and_nonblank():
    ids = [i.pcpp_product_id for i in _mapped_items()]
    assert all(pid and pid.strip() for pid in ids)
    assert len(ids) == len(set(ids)), "pcpp_product_id values must be unique"


def test_mappings_table_records_product_name_for_traceability():
    # Each mapped catalog name -> (pcpp_product_id, pcpp_product_name) for audit.
    for name, (pid, pname) in PCPP_MAPPINGS.items():
        assert HardwareCatalog.get_by_name(name) is not None, f"unknown catalog item: {name}"
        assert pid and pname, f"mapping for {name} missing id or product name"
    # The registry and the applied catalog agree.
    applied = {i.name: i.pcpp_product_id for i in _mapped_items()}
    assert applied == {name: pid for name, (pid, _pname) in PCPP_MAPPINGS.items()}


def test_enterprise_used_only_skus_stay_null():
    # Representative used-only / enterprise SKUs that should NOT be mapped.
    for name in ("AMD EPYC 7F72", "Intel P5510 1.92TB U.2"):
        item = HardwareCatalog.get_by_name(name)
        assert item is not None
        assert getattr(item, "pcpp_product_id", None) is None, f"{name} should stay unmapped"


def test_mapping_round_trips_into_tracked_item():
    # A mapped catalog item builds a TrackedItem carrying the pcpp id (no schema
    # change needed — the column pre-exists).
    mapped = _mapped_items()[0]
    ti = TrackedItem(
        name=mapped.name, keywords=mapped.keywords,
        benchmark_median=mapped.benchmark_median, scam_floor=mapped.scam_floor,
        pcpp_product_id=mapped.pcpp_product_id,
    )
    assert ti.pcpp_product_id == mapped.pcpp_product_id


def _load_generator():
    gen_path = BACKEND_DIR / "scripts" / "generate_seed.py"
    spec = importlib.util.spec_from_file_location("generate_seed", gen_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_generated_seed_includes_pcpp_product_id_column_and_values():
    gen = _load_generator()
    sql = gen.render_sql()
    assert "pcpp_product_id" in sql, "seed must include the pcpp_product_id column"
    # At least one mapped id literal appears in the generated SQL.
    sample = _mapped_items()[0].pcpp_product_id
    assert f"'{sample}'" in sql


async def test_seeded_tracked_items_get_pcpp_id(db):
    # Build TrackedItems directly from the catalog (mirrors what the seed does)
    # and verify the mapped ones land their pcpp_product_id after a round-trip.
    for ci in HardwareCatalog.ITEMS:
        db.add(TrackedItem(
            name=ci.name, keywords=ci.keywords, benchmark_median=ci.benchmark_median,
            scam_floor=ci.scam_floor, pcpp_product_id=getattr(ci, "pcpp_product_id", None),
        ))
    await db.flush()
    rows = (await db.execute(select(TrackedItem).where(TrackedItem.pcpp_product_id.is_not(None)))).scalars().all()
    assert len(rows) == 7
