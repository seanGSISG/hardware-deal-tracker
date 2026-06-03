"""T3.5 — the tracked_items seed must be idempotent.

Re-running the seed (e.g. on every container start) must not raise duplicate-key
errors or double-insert the catalog. We assert the INSERT carries an ON CONFLICT
clause keyed on `name`, and that the model backs it with a unique constraint so the
clause is actually enforceable in Postgres.
"""
from pathlib import Path

from app.models.tracked_item import TrackedItem

SEED = Path(__file__).resolve().parents[1] / "scripts" / "seed_data_v2.sql"


def test_seed_file_exists():
    assert SEED.is_file()


def test_tracked_items_insert_is_idempotent():
    sql = SEED.read_text().lower()
    assert "insert into tracked_items" in sql
    # The tracked_items insert must be guarded by an ON CONFLICT (name) clause.
    insert_idx = sql.index("insert into tracked_items")
    # Look at the statement body up to its terminating semicolon.
    stmt = sql[insert_idx : sql.index(";", insert_idx)]
    assert "on conflict (name)" in stmt
    assert "do nothing" in stmt or "do update" in stmt


def test_name_column_is_unique():
    # ON CONFLICT (name) requires a unique constraint/index on name.
    assert TrackedItem.__table__.columns["name"].unique is True
