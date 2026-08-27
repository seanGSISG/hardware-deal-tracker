"""Catalog <-> generated seed parity.

`scripts/generate_seed.py` is the single generator: it reads the Python
HardwareCatalog (the source of truth) and writes a deterministic, idempotent
`scripts/seed_data_v2.sql`. These tests assert the committed SQL is in sync with
the catalog and that the generator output is stable/idempotent.
"""
import importlib.util
import re
from pathlib import Path

import pytest

from app.services.ebay.catalog import HardwareCatalog

BACKEND_DIR = Path(__file__).resolve().parent.parent
SEED_PATH = BACKEND_DIR / "scripts" / "seed_data_v2.sql"
GEN_PATH = BACKEND_DIR / "scripts" / "generate_seed.py"


def _load_generator():
    spec = importlib.util.spec_from_file_location("generate_seed", GEN_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_generator_exists():
    assert GEN_PATH.exists(), "scripts/generate_seed.py must exist"


def test_generated_sql_is_idempotent_on_conflict():
    gen = _load_generator()
    sql = gen.render_sql()
    # Every tracked_items INSERT block must carry an ON CONFLICT (name) clause.
    assert "INSERT INTO tracked_items" in sql
    assert "ON CONFLICT (name)" in sql


def test_generated_sql_contains_every_catalog_item():
    gen = _load_generator()
    sql = gen.render_sql()
    for item in HardwareCatalog.ITEMS:
        # Names may contain SQL-escaped single quotes.
        escaped = item.name.replace("'", "''")
        assert f"('{escaped}'" in sql, f"missing catalog item in seed: {item.name}"


def test_generated_row_count_matches_catalog():
    gen = _load_generator()
    sql = gen.render_sql()
    # Count tracked_items value rows in the dedicated tracked_items section only
    # (the file also contains users + notification_settings rows).
    # Bound the section at ON CONFLICT, not the first ";": a semicolon inside a
    # quoted notes string is legal SQL and silently truncated the row count.
    section = sql.split("INSERT INTO tracked_items", 1)[1].split("ON CONFLICT", 1)[0]
    value_rows = re.findall(r"^\s*\('", section, flags=re.MULTILINE)
    assert len(value_rows) == len(HardwareCatalog.ITEMS)


def test_generator_is_deterministic():
    gen = _load_generator()
    assert gen.render_sql() == gen.render_sql()


def test_committed_seed_is_in_sync_with_catalog():
    """The committed seed_data_v2.sql must equal freshly generated output.

    If this fails, run `make seed-regen` and commit the result.
    """
    if not SEED_PATH.exists():
        pytest.skip("seed file missing")
    gen = _load_generator()
    expected = gen.render_sql()
    actual = SEED_PATH.read_text()
    assert actual == expected, "seed_data_v2.sql is stale; run `make seed-regen`"
