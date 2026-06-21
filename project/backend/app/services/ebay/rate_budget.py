import logging
from datetime import datetime

from app.core.config import settings

logger = logging.getLogger(__name__)


class RateBudgetManager:
    """Tracks and enforces the daily eBay API call budget."""

    DAILY_LIMIT: int = settings.EBAY_DAILY_CALL_LIMIT
    BUFFER: int = settings.EBAY_CALL_BUFFER
    NEAR_LIMIT: int = settings.EBAY_NEAR_LIMIT_THRESHOLD

    def __init__(self, redis_client=None):
        self.redis = redis_client
        self._memory_count = 0
        self._memory_date = datetime.utcnow().date()

    def _key(self) -> str:
        return f"ebay_calls:{datetime.utcnow().strftime('%Y%m%d')}"

    def _memory_count_today(self) -> int:
        if datetime.utcnow().date() != self._memory_date:
            self._memory_count = 0
            self._memory_date = datetime.utcnow().date()
        return self._memory_count

    async def get_today_count(self) -> int:
        if self.redis:
            try:
                count = await self.redis.get(self._key())
                return int(count) if count else 0
            except Exception:  # noqa: BLE001 — a redis blip must never halt the poll
                logger.warning("redis get failed; using in-memory budget count", exc_info=True)
        return self._memory_count_today()

    async def record_call(self):
        if self.redis:
            try:
                pipe = self.redis.pipeline()
                pipe.incr(self._key())
                pipe.expire(self._key(), 86400)
                await pipe.execute()
                return
            except Exception:  # noqa: BLE001 — degrade to in-memory, never raise
                logger.warning("redis incr failed; using in-memory budget count", exc_info=True)
        self._memory_count = self._memory_count_today() + 1

    async def can_search(self, priority: str = "P1") -> bool:
        count = await self.get_today_count()
        if count >= self.DAILY_LIMIT - self.BUFFER:
            return False
        return not (count >= self.NEAR_LIMIT and priority not in ("P0",))

    async def get_budget_status(self) -> dict:
        count = await self.get_today_count()
        remaining = self.DAILY_LIMIT - count
        return {
            "calls_today": count,
            "daily_limit": self.DAILY_LIMIT,
            "remaining": remaining,
            "buffer": self.BUFFER,
            "utilization_pct": round(count / self.DAILY_LIMIT * 100, 1),
            "status": "ok" if remaining > self.BUFFER else "critical" if remaining <= 0 else "warning",
            "searches_possible": remaining - self.BUFFER,
        }

    def get_priority_for_interval(self, interval: int) -> str:
        if interval <= 360:
            return "P0"
        elif interval <= 600:
            return "P1"
        elif interval <= 1200:
            return "P2"
        return "P3"
