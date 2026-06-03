"""T3.6 — RateBudgetManager budget gates (4-layer rate limiting).

Verifies the three call-budget boundaries the plan calls out:
  * 200-call buffer => hard stop at DAILY_LIMIT - BUFFER (4800), regardless of priority.
  * near-limit threshold (4000): P1+ searches are skipped, P0 (hot) is still allowed.
  * 5000 daily limit => hard stop for everything.

The manager runs in memory mode (no redis); we drive the count via the public
record path / a monkeypatched counter so we exercise can_search exactly as the
poller does.
"""
import pytest

from app.services.ebay.rate_budget import RateBudgetManager


def _mgr_at(monkeypatch, count: int) -> RateBudgetManager:
    """A memory-mode manager whose get_today_count returns a fixed value."""
    mgr = RateBudgetManager()

    async def _count(self):
        return count

    monkeypatch.setattr(RateBudgetManager, "get_today_count", _count)
    return mgr


async def test_plenty_of_budget_allows_all_priorities(monkeypatch):
    mgr = _mgr_at(monkeypatch, 0)
    for prio in ("P0", "P1", "P2", "P3"):
        assert await mgr.can_search(prio) is True


async def test_near_limit_skips_p1_but_allows_p0(monkeypatch):
    # At the 4000 near-limit threshold, only P0 (hot) traffic is permitted.
    mgr = _mgr_at(monkeypatch, 4000)
    assert await mgr.can_search("P0") is True
    assert await mgr.can_search("P1") is False
    assert await mgr.can_search("P2") is False
    assert await mgr.can_search("P3") is False


async def test_buffer_hard_stop_blocks_even_p0(monkeypatch):
    # DAILY_LIMIT - BUFFER = 5000 - 200 = 4800 is the hard stop for ALL priorities.
    mgr = _mgr_at(monkeypatch, 4800)
    assert await mgr.can_search("P0") is False
    assert await mgr.can_search("P1") is False


async def test_daily_limit_hard_stop(monkeypatch):
    mgr = _mgr_at(monkeypatch, 5000)
    assert await mgr.can_search("P0") is False
    assert await mgr.can_search("P1") is False


async def test_budget_status_reports_utilization(monkeypatch):
    mgr = _mgr_at(monkeypatch, 2500)
    status = await mgr.get_budget_status()
    assert status["calls_today"] == 2500
    assert status["daily_limit"] == 5000
    assert status["remaining"] == 2500
    assert status["utilization_pct"] == pytest.approx(50.0)


async def test_record_call_increments_memory_counter():
    mgr = RateBudgetManager()
    start = await mgr.get_today_count()
    await mgr.record_call()
    assert await mgr.get_today_count() == start + 1
