from datetime import datetime, timedelta
from statistics import median

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.item_price_baseline import ItemPriceBaseline
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

    # feature-001: surface the resolved rolling baseline + trend (ADR-001) so
    # feature-005 can render a baseline band/trend chip and the AI panel can cite
    # the median/IQR. Additive-only; degrades to nulls + benchmark when no usable
    # snapshot exists.
    baseline_row = (
        await db.execute(
            select(ItemPriceBaseline).where(ItemPriceBaseline.tracked_item_id == item_id)
        )
    ).scalar_one_or_none()
    benchmark_median = float(item.benchmark_median) if item.benchmark_median is not None else None

    if baseline_row is not None and baseline_row.median_price is not None:
        base_median = float(baseline_row.median_price)
        baseline_vs_median_pct = (
            round((base_median - latest_total) / base_median, 4)
            if base_median and latest_total is not None
            else None
        )
        baseline = {
            "median": base_median,
            "avg": float(baseline_row.avg_price) if baseline_row.avg_price is not None else None,
            "std_dev": float(baseline_row.std_dev) if baseline_row.std_dev is not None else None,
            "min": float(baseline_row.min_price) if baseline_row.min_price is not None else None,
            "q1": float(baseline_row.q1) if baseline_row.q1 is not None else None,
            "q3": float(baseline_row.q3) if baseline_row.q3 is not None else None,
            "data_points": int(baseline_row.data_points or 0),
            "lookback_days": baseline_row.lookback_days,
            "vs_median_pct": baseline_vs_median_pct,
            "source": baseline_row.source,
            "trend_direction": baseline_row.trend_direction,
            "trend_slope_pct": (
                float(baseline_row.trend_slope_pct)
                if baseline_row.trend_slope_pct is not None
                else None
            ),
            "computed_at": baseline_row.computed_at.isoformat() if baseline_row.computed_at else None,
            "benchmark_median": benchmark_median,
        }
    else:
        # No usable snapshot: degrade to nulls + the catalog benchmark, preserving
        # any persisted trend/source on a benchmark-sourced row.
        baseline = {
            "median": None,
            "avg": None,
            "std_dev": None,
            "min": None,
            "q1": None,
            "q3": None,
            "data_points": int(baseline_row.data_points or 0) if baseline_row is not None else 0,
            "lookback_days": baseline_row.lookback_days if baseline_row is not None else None,
            "vs_median_pct": None,
            "source": baseline_row.source if baseline_row is not None else "benchmark",
            "trend_direction": baseline_row.trend_direction if baseline_row is not None else None,
            "trend_slope_pct": (
                float(baseline_row.trend_slope_pct)
                if baseline_row is not None and baseline_row.trend_slope_pct is not None
                else None
            ),
            "computed_at": (
                baseline_row.computed_at.isoformat()
                if baseline_row is not None and baseline_row.computed_at
                else None
            ),
            "benchmark_median": benchmark_median,
        }

    return {
        "item_id": item_id,
        "days": days,
        "count": len(points),
        "points": points,
        "median_total": median_total,
        "latest_total": latest_total,
        "vs_median_pct": vs_median_pct,
        "benchmark_median": benchmark_median,
        "baseline": baseline,
    }
