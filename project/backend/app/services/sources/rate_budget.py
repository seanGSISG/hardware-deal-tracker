"""Per-source rate budgeting (feature-005, story-F).

eBay has its own 5000/day `RateBudgetManager`. Every *other* source (PCPartPicker,
Shopify retailers) gets a small, polite, self-imposed daily bucket here, so a slow
benchmark/enrichment source can never eat into eBay's budget and each source can
be tuned/disabled independently. In-memory by design — these limits are tiny and
advisory; persistence/Redis can be layered on later if needed.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date


@dataclass
class _Bucket:
    daily_limit: int
    count: int = 0
    day: date = field(default_factory=date.today)

    def _roll(self) -> None:
        today = date.today()
        if today != self.day:
            self.day = today
            self.count = 0


class SourceRateBudget:
    """Independent per-source daily call buckets."""

    def __init__(self, default_daily_limit: int = 200):
        self.default_daily_limit = default_daily_limit
        self._buckets: dict[str, _Bucket] = {}

    def configure(self, source: str, daily_limit: int) -> None:
        self._buckets[source] = _Bucket(daily_limit=daily_limit)

    def _bucket(self, source: str) -> _Bucket:
        bucket = self._buckets.get(source)
        if bucket is None:
            bucket = _Bucket(daily_limit=self.default_daily_limit)
            self._buckets[source] = bucket
        bucket._roll()
        return bucket

    def can_call(self, source: str) -> bool:
        bucket = self._bucket(source)
        return bucket.count < bucket.daily_limit

    def record_call(self, source: str) -> None:
        bucket = self._bucket(source)
        bucket.count += 1

    def status(self, source: str) -> dict:
        bucket = self._bucket(source)
        return {
            "source": source,
            "calls_today": bucket.count,
            "daily_limit": bucket.daily_limit,
            "remaining": max(0, bucket.daily_limit - bucket.count),
        }
