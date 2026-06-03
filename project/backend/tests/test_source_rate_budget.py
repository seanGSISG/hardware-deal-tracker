"""story-F: per-source rate budgeting.

Non-eBay sources (PCPartPicker, Shopify retailers) get their own polite,
self-imposed daily call buckets — separate from eBay's 5000/day budget — so a
slow benchmark source can never eat into the eBay budget and vice-versa.
"""
from app.services.sources.rate_budget import SourceRateBudget


def test_separate_buckets_are_independent():
    budget = SourceRateBudget()
    budget.configure("pcpartpicker", daily_limit=3)
    budget.configure("techmikeny", daily_limit=2)

    # pcpartpicker bucket
    assert budget.can_call("pcpartpicker") is True
    for _ in range(3):
        budget.record_call("pcpartpicker")
    assert budget.can_call("pcpartpicker") is False

    # techmikeny bucket is untouched by pcpartpicker usage
    assert budget.can_call("techmikeny") is True


def test_unconfigured_source_uses_default_limit():
    budget = SourceRateBudget(default_daily_limit=1)
    assert budget.can_call("brand_new_source") is True
    budget.record_call("brand_new_source")
    assert budget.can_call("brand_new_source") is False


def test_count_and_remaining_reported():
    budget = SourceRateBudget()
    budget.configure("pcpartpicker", daily_limit=200)
    budget.record_call("pcpartpicker")
    budget.record_call("pcpartpicker")

    status = budget.status("pcpartpicker")
    assert status["calls_today"] == 2
    assert status["daily_limit"] == 200
    assert status["remaining"] == 198


def test_does_not_share_with_ebay_5000_budget():
    # The per-source budget must not default to eBay's 5000 — these are polite
    # self-imposed limits, much smaller.
    budget = SourceRateBudget(default_daily_limit=200)
    assert budget.status("anything")["daily_limit"] != 5000


def test_daily_rollover_resets_count(monkeypatch):
    import app.services.sources.rate_budget as rb_mod

    budget = SourceRateBudget()
    budget.configure("pcpartpicker", daily_limit=1)

    budget.record_call("pcpartpicker")
    assert budget.can_call("pcpartpicker") is False

    # Simulate the next day.
    import datetime as _dt

    class _Tomorrow(_dt.date):
        @classmethod
        def today(cls):
            return _dt.date(2999, 1, 1)

    monkeypatch.setattr(rb_mod, "date", _Tomorrow)
    assert budget.can_call("pcpartpicker") is True
