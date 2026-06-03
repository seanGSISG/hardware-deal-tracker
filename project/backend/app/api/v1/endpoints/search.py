from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.core import metrics
from app.models.tracked_item import TrackedItem
from app.models.user import User
from app.services.ebay.poller import EbayPoller

router = APIRouter(prefix="/search", tags=["search"])


def _seconds_until_budget_reset() -> int:
    """Seconds until the daily eBay call budget resets (next UTC midnight)."""
    now = datetime.now(UTC)
    next_midnight = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    return max(1, int((next_midnight - now).total_seconds()))


def _budget_exhausted_response() -> JSONResponse:
    metrics.EBAY_RATE_LIMITED.inc()
    retry_after = _seconds_until_budget_reset()
    return JSONResponse(
        status_code=429,
        content={"detail": "eBay rate budget exhausted", "retry_after": retry_after},
        headers={"Retry-After": str(retry_after)},
    )


@router.post("/trigger/{item_id}")
async def trigger_search(
    item_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    item = await db.get(TrackedItem, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    poller = EbayPoller()
    result = await poller.search_item(db, item)
    if result.get("skipped"):
        return _budget_exhausted_response()
    await db.commit()
    return result


@router.post("/trigger-all")
async def trigger_all(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    poller = EbayPoller()
    # If even the highest-priority tier can't search, the budget is exhausted.
    if not await poller.budget.can_search("P0"):
        return _budget_exhausted_response()

    result = await poller.search_all(db)
    await db.commit()
    return result


@router.get("/budget")
async def get_budget(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    poller = EbayPoller()
    status = await poller.get_budget_status()
    metrics.update_rate_budget(status)
    return status


@router.get("/presets")
async def get_presets(user: User = Depends(get_current_user)):
    return {
        "presets": {
            "hot": {"interval": 300, "label": "Hot (5 min)", "daily_calls": 288},
            "standard": {"interval": 600, "label": "Standard (10 min)", "daily_calls": 144},
            "monitor": {"interval": 1200, "label": "Monitor (20 min)", "daily_calls": 72},
            "passive": {"interval": 1800, "label": "Passive (30 min)", "daily_calls": 48},
        }
    }
