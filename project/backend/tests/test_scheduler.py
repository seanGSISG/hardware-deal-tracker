"""story-003: FastAPI lifespan + in-process APScheduler v3 poll tick (ADR-001)."""
from apscheduler.schedulers.asyncio import AsyncIOScheduler

import app.main as main_mod
from app.core.config import settings


class _RecordingScheduler(AsyncIOScheduler):
    """AsyncIOScheduler that records shutdown(wait=...) invocations for assertion.

    (AsyncIOScheduler.shutdown defers the state flip via the event loop, so a
    spy is more reliable than polling .running immediately after exit.)"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.shutdown_calls = []

    def shutdown(self, wait=True):
        self.shutdown_calls.append(wait)
        super().shutdown(wait)


class _FakeSession:
    async def commit(self):
        pass


class _FakeSessionCtx:
    async def __aenter__(self):
        return _FakeSession()

    async def __aexit__(self, *exc):
        return False


async def test_lifespan_registers_single_poll_job(monkeypatch):
    monkeypatch.setattr(settings, "SCHEDULER_ENABLED", True)
    monkeypatch.setattr(settings, "POLL_SCHEDULER_INTERVAL", 123)
    monkeypatch.setattr(main_mod, "AsyncIOScheduler", _RecordingScheduler)

    async with main_mod.lifespan(main_mod.app):
        scheduler = main_mod.app.state.scheduler
        assert scheduler is not None
        assert scheduler.running is True
        jobs = scheduler.get_jobs()
        assert len(jobs) == 1
        job = scheduler.get_job("poll_tick")
        assert job is not None
        assert job.trigger.interval.total_seconds() == 123
        assert job.coalesce is True
        assert job.max_instances == 1

    # On lifespan exit the scheduler is shut down with wait=False.
    assert scheduler.shutdown_calls == [False]


async def test_lifespan_disabled_registers_no_job(monkeypatch):
    monkeypatch.setattr(settings, "SCHEDULER_ENABLED", False)

    async with main_mod.lifespan(main_mod.app):
        assert getattr(main_mod.app.state, "scheduler", None) is None


async def test_poll_tick_invokes_search_all_once(monkeypatch):
    calls = {"n": 0}

    class FakePoller:
        async def search_all(self, db):
            calls["n"] += 1
            return {"items_processed": 1, "total_new": 2, "items_skipped": 0}

    monkeypatch.setattr(main_mod, "session_factory", lambda: _FakeSessionCtx())
    monkeypatch.setattr(main_mod, "EbayPoller", lambda *a, **k: FakePoller())

    await main_mod._poll_tick()
    assert calls["n"] == 1


async def test_poll_tick_swallows_search_all_errors(monkeypatch):
    class BoomPoller:
        async def search_all(self, db):
            raise RuntimeError("boom")

    monkeypatch.setattr(main_mod, "session_factory", lambda: _FakeSessionCtx())
    monkeypatch.setattr(main_mod, "EbayPoller", lambda *a, **k: BoomPoller())

    # Must not propagate — a failing tick may never kill the scheduler.
    await main_mod._poll_tick()
