from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.models.tracked_item import TrackedItem

router = APIRouter(prefix="/search", tags=["search"])


@router.post("/trigger/{item_id}")
async def trigger_search(
    item_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    result = await db.execute(select(TrackedItem).where(TrackedItem.id == item_id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return {"listings_found": 0, "new_listings": 0, "duplicates_skipped": 0, "duration_ms": 0}


@router.post("/trigger-all")
async def trigger_all(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    return {"items_processed": 0, "total_listings": 0, "total_new": 0, "total_duplicates": 0}


@router.get("/budget")
async def get_budget(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    return {
        "calls_today": 0,
        "daily_limit": 5000,
        "remaining": 5000,
        "buffer": 200,
        "utilization_pct": 0.0,
        "status": "ok",
        "searches_possible": 4800,
    }


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
