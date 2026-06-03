from datetime import datetime, timedelta
from statistics import median

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.price_history import PriceHistory
from app.models.tracked_item import TrackedItem
from app.models.user import User

router = APIRouter(prefix="/price-history", tags=["price-history"])


@router.get("/{item_id}")
async def get_price_history(
    item_id: int,
    days: int = Query(90, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    item = await db.get(TrackedItem, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    since = datetime.utcnow() - timedelta(days=days)
    rows = (
        await db.execute(
            select(PriceHistory)
            .where(PriceHistory.tracked_item_id == item_id)
            .where(PriceHistory.timestamp >= since)
            .order_by(PriceHistory.timestamp.asc())
        )
    ).scalars().all()

    points = [
        {
            "timestamp": p.timestamp.isoformat() if p.timestamp else None,
            "observed_price": float(p.observed_price),
            "shipping": float(p.shipping),
            "total_price": float(p.total_price),
        }
        for p in rows
    ]
    totals = [pt["total_price"] for pt in points]
    median_total = round(median(totals), 2) if totals else None
    latest_total = points[-1]["total_price"] if points else None
    vs_median_pct = (
        round((median_total - latest_total) / median_total, 4)
        if median_total and latest_total is not None
        else None
    )

    return {
        "item_id": item_id,
        "days": days,
        "count": len(points),
        "points": points,
        "median_total": median_total,
        "latest_total": latest_total,
        "vs_median_pct": vs_median_pct,
        "benchmark_median": float(item.benchmark_median) if item.benchmark_median is not None else None,
    }
