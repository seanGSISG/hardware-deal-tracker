import redis.asyncio as aioredis

from app.core.config import settings

_redis_client: aioredis.Redis | None = None


def get_redis_client() -> aioredis.Redis:
    """Shared async Redis client (lazy singleton, pooled connections).

    The eBay daily-call budget (RateBudgetManager) needs this to persist its
    count in Redis (key ``ebay_calls:YYYYMMDD``) across poll ticks and API
    requests. Without a client each freshly-constructed EbayPoller falls back to
    a per-instance in-memory counter that resets to 0 every time — which is why
    the dashboard "eBay API n / 5,000" meter always read 0.
    """
    global _redis_client
    if _redis_client is None:
        _redis_client = aioredis.from_url(
            settings.REDIS_URL, encoding="utf-8", decode_responses=True
        )
    return _redis_client
