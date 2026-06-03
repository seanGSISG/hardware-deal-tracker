"""T3.3 — server_default audit.

Columns that have a Python-side `default=` but no `server_default=` get NULL when a
row is inserted outside the ORM (raw SQL seed, psql, another service). This locks in
DB-level defaults for the booleans/enums the app assumes are always populated.
"""
import pytest

from app.models.tracked_item import TrackedItem
from app.models.user import User

TRACKED_ITEM_COLS = [
    "marketplace",
    "alert_threshold",
    "min_deal_score",
    "is_enabled",
    "search_interval",
]
USER_COLS = ["is_active", "is_admin"]


@pytest.mark.parametrize("col", TRACKED_ITEM_COLS)
def test_tracked_item_columns_have_server_default(col):
    column = TrackedItem.__table__.columns[col]
    assert column.server_default is not None, f"TrackedItem.{col} missing server_default"


@pytest.mark.parametrize("col", USER_COLS)
def test_user_columns_have_server_default(col):
    column = User.__table__.columns[col]
    assert column.server_default is not None, f"User.{col} missing server_default"
