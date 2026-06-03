"""feature-001 story-006: daily baseline_refresh_tick scheduler job.

TDD: written FIRST. The tick refreshes ItemPriceBaseline rows for enabled items
and is best-effort (one item's failure never aborts the rest). The job is
registered with a distinct id gated by SCHEDULER_ENABLED + BASELINE_REFRESH_ENABLED.
"""
from datetime import datetime, timedelta

from sqlalchemy import select

import app.main as main_mod
from app.core.config import settings
from app.models.item_price_baseline import ItemPriceBaseline
from app.models.listing import Listing
from app.models.price_history import PriceHistory
from app.models.tracked_item import TrackedItem


class _RecordingScheduler:
    """Minimal scheduler stub that records add_job calls (no real loop)."""

    def __init__(self, *a, **k):
        self.jobs = {}

    def add_job(self, func, trigger=None, id=None, **kwargs):
        self.jobs[id] = {"func": func, "trigger": trigger, "kwargs": kwargs}

    def get_jobs(self):
        return [type("J", (), {"id": jid}) for jid in self.jobs]

    def get_job(self, jid):
        return self.jobs.get(jid)

    def start(self):
        pass

    def shutdown(self, wait=True):
        pass

    @property
    def running(self):
        return True


async def _seed_enabled_item_with_history(db, name, totals):
    item = TrackedItem(
        name=name, keywords=name, benchmark_median=350, scam_floor=10,
        search_interval=600, is_enabled=True,
    )
    db.add(item)
    await db.flush()
    listing = Listing(
        marketplace_id=f"m_{name}", tracked_item_id=item.id, title="x", price=100,
        shipping=0, seller="s", url="u", listing_date=datetime.utcnow(),
    )
    db.add(listing)
    await db.flush()
    base = datetime.utcnow() - timedelta(days=10)
    for i, total in enumerate(totals):
        db.add(PriceHistory(
            listing_id=listing.id, tracked_item_id=item.id,
            observed_price=total, shipping=0, total_price=total,
            timestamp=base + timedelta(days=i),
        ))
    await db.flush()
    return item


async def test_baseline_refresh_tick_upserts_for_enabled_items(db, monkeypatch):
    a = await _seed_enabled_item_with_history(db, "ItemA", [300, 305, 295, 310, 290, 300, 308, 302])
    b = await _seed_enabled_item_with_history(db, "ItemB", [200, 205, 195, 210, 190, 200, 208, 202])

    class _Ctx:
        async def __aenter__(self):
            return db

        async def __aexit__(self, *exc):
            return False

    monkeypatch.setattr(main_mod, "session_factory", lambda: _Ctx())

    await main_mod._baseline_refresh_tick()

    rows = (await db.execute(select(ItemPriceBaseline))).scalars().all()
    by_item = {r.tracked_item_id: r for r in rows}
    assert a.id in by_item and b.id in by_item
    assert by_item[a.id].source == "price_history"
    assert by_item[b.id].source == "price_history"


async def test_baseline_refresh_tick_is_best_effort(db, monkeypatch):
    """A failure in one item's refresh is caught/logged without aborting the rest."""
    good = await _seed_enabled_item_with_history(db, "Good", [300, 305, 295, 310, 290, 300, 308, 302])
    await _seed_enabled_item_with_history(db, "Bad", [100, 105, 95, 110, 90, 100, 108, 102])

    class _Ctx:
        async def __aenter__(self):
            return db

        async def __aexit__(self, *exc):
            return False

    monkeypatch.setattr(main_mod, "session_factory", lambda: _Ctx())

    from app.services.scoring.baseline_service import ScoringBaselineService
    real_refresh = ScoringBaselineService.refresh_item

    async def _flaky(self, db_, item):
        if item.name == "Bad":
            raise RuntimeError("boom")
        return await real_refresh(self, db_, item)

    monkeypatch.setattr(ScoringBaselineService, "refresh_item", _flaky)

    # Must not raise despite the Bad item blowing up.
    await main_mod._baseline_refresh_tick()

    rows = (await db.execute(select(ItemPriceBaseline))).scalars().all()
    names = {good.id}
    assert any(r.tracked_item_id in names and r.source == "price_history" for r in rows)


async def test_baseline_refresh_tick_swallows_top_level_errors(monkeypatch):
    class _BoomCtx:
        async def __aenter__(self):
            raise RuntimeError("db down")

        async def __aexit__(self, *exc):
            return False

    monkeypatch.setattr(main_mod, "session_factory", lambda: _BoomCtx())
    # Must not propagate — a failing tick may never kill the scheduler.
    await main_mod._baseline_refresh_tick()


async def test_lifespan_registers_baseline_job(monkeypatch):
    monkeypatch.setattr(settings, "SECRET_KEY", "x" * 48)
    monkeypatch.setattr(settings, "SCHEDULER_ENABLED", True)
    monkeypatch.setattr(settings, "BASELINE_REFRESH_ENABLED", True)
    monkeypatch.setattr(settings, "BASELINE_REFRESH_HOUR", 6)
    monkeypatch.setattr(main_mod, "AsyncIOScheduler", _RecordingScheduler)

    async with main_mod.lifespan(main_mod.app):
        scheduler = main_mod.app.state.scheduler
        ids = {j.id for j in scheduler.get_jobs()}
        assert "baseline_refresh_tick" in ids
        # poll_tick is untouched.
        assert "poll_tick" in ids


async def test_lifespan_skips_baseline_job_when_disabled(monkeypatch):
    monkeypatch.setattr(settings, "SECRET_KEY", "x" * 48)
    monkeypatch.setattr(settings, "SCHEDULER_ENABLED", True)
    monkeypatch.setattr(settings, "BASELINE_REFRESH_ENABLED", False)
    monkeypatch.setattr(main_mod, "AsyncIOScheduler", _RecordingScheduler)

    async with main_mod.lifespan(main_mod.app):
        ids = {j.id for j in main_mod.app.state.scheduler.get_jobs()}
        assert "baseline_refresh_tick" not in ids
        assert "poll_tick" in ids
