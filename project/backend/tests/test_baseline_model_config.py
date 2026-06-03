"""feature-001 story-003: BASELINE_* config vars + ItemPriceBaseline model.

TDD: written FIRST. Asserts (a) the new BASELINE_* settings expose the documented
defaults and (b) an ItemPriceBaseline row can be created/queried against the
in-memory test DB with the unique-per-item constraint enforced.
"""
import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.core.config import Settings


def test_baseline_settings_defaults():
    s = Settings()
    assert s.BASELINE_LOOKBACK_DAYS == 90
    assert s.BASELINE_TUKEY_K == 1.5
    assert s.BASELINE_MIN_POINTS == 5
    assert s.BASELINE_TREND_WINDOW_DAYS == 30
    assert s.BASELINE_TREND_THRESHOLD_PCT == 0.05
    assert s.BASELINE_REFRESH_ENABLED is True
    assert s.BASELINE_REFRESH_HOUR == 6


def test_baseline_settings_env_override(monkeypatch):
    monkeypatch.setenv("BASELINE_LOOKBACK_DAYS", "120")
    monkeypatch.setenv("BASELINE_TUKEY_K", "2.0")
    monkeypatch.setenv("BASELINE_MIN_POINTS", "8")
    monkeypatch.setenv("BASELINE_TREND_THRESHOLD_PCT", "0.1")
    monkeypatch.setenv("BASELINE_REFRESH_ENABLED", "false")
    monkeypatch.setenv("BASELINE_REFRESH_HOUR", "3")
    s = Settings()
    assert s.BASELINE_LOOKBACK_DAYS == 120
    assert s.BASELINE_TUKEY_K == 2.0
    assert s.BASELINE_MIN_POINTS == 8
    assert s.BASELINE_TREND_THRESHOLD_PCT == 0.1
    assert s.BASELINE_REFRESH_ENABLED is False
    assert s.BASELINE_REFRESH_HOUR == 3


def test_existing_settings_preserved():
    # Additive only — pre-existing fields keep identical defaults.
    s = Settings()
    assert s.SCHEDULER_ENABLED is True
    assert s.POLL_SCHEDULER_INTERVAL == 300
    assert s.USE_MOCK_EBAY is True


def test_item_price_baseline_is_registered():
    from app import models
    assert "ItemPriceBaseline" in models.__all__
    from app.models.item_price_baseline import ItemPriceBaseline
    assert ItemPriceBaseline.__tablename__ == "item_price_baselines"


async def _seed_item(db):
    from app.models.tracked_item import TrackedItem
    item = TrackedItem(
        name="EPYC 7F72", keywords="EPYC 7F72", benchmark_median=350,
        scam_floor=10, search_interval=600, is_enabled=True,
    )
    db.add(item)
    await db.flush()
    return item


async def test_item_price_baseline_create_and_query(db):
    from app.models.item_price_baseline import ItemPriceBaseline
    item = await _seed_item(db)
    row = ItemPriceBaseline(
        tracked_item_id=item.id,
        median_price=300.0, avg_price=305.0, std_dev=12.0, min_price=280.0,
        q1=295.0, q3=315.0, data_points=20, lookback_days=90,
        trend_direction="stable", trend_slope_pct=0.0, source="price_history",
    )
    db.add(row)
    await db.flush()

    fetched = (
        await db.execute(
            select(ItemPriceBaseline).where(ItemPriceBaseline.tracked_item_id == item.id)
        )
    ).scalar_one()
    assert fetched.median_price == 300.0
    assert fetched.source == "price_history"
    assert fetched.trend_direction == "stable"
    assert fetched.computed_at is not None


async def test_item_price_baseline_unique_per_item(db):
    from app.models.item_price_baseline import ItemPriceBaseline
    item = await _seed_item(db)
    db.add(ItemPriceBaseline(tracked_item_id=item.id, median_price=1, source="benchmark"))
    await db.flush()
    db.add(ItemPriceBaseline(tracked_item_id=item.id, median_price=2, source="benchmark"))
    with pytest.raises(IntegrityError):
        await db.flush()
