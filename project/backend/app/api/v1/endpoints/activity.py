from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.search_log import SearchLog
from app.models.user import User

router = APIRouter(prefix="/activity", tags=["activity"])


def _serialize(row: SearchLog) -> dict:
    return {
        "id": row.id,
        "tracked_item_id": row.tracked_item_id,
        "item_name": row.item_name,
        "source": row.source,
        "status": row.status,
        "priority": row.priority,
        "listings_found": row.listings_found,
        "new_listings": row.new_listings,
        "duplicates": row.duplicates,
        "calls_used": row.calls_used,
        "duration_ms": row.duration_ms,
        "detail": row.detail,
        "created_at": row.created_at.isoformat() if row.created_at else None,
    }


@router.get("")
async def list_activity(
    status: str | None = Query(None, description="ok | skipped | error"),
    source: str | None = None,
    item_id: int | None = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Paginated activity log — one row per per-item search, newest first."""
    query = select(SearchLog).order_by(SearchLog.created_at.desc(), SearchLog.id.desc())
    if status:
        query = query.where(SearchLog.status == status)
    if source:
        query = query.where(SearchLog.source == source)
    if item_id:
        query = query.where(SearchLog.tracked_item_id == item_id)

    total = (
        await db.execute(select(func.count()).select_from(query.subquery()))
    ).scalar() or 0

    rows = (
        await db.execute(query.offset((page - 1) * per_page).limit(per_page))
    ).scalars().all()

    return {
        "total": total,
        "page": page,
        "per_page": per_page,
        "entries": [_serialize(r) for r in rows],
    }


@router.get("/summary")
async def activity_summary(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Header stats for the Activity page: recency + last-24h rollups."""
    now = datetime.now(UTC)
    since_24h = now - timedelta(hours=24)
    since_1h = now - timedelta(hours=1)

    last_search_at = (
        await db.execute(select(func.max(SearchLog.created_at)))
    ).scalar()

    async def _count(*conds) -> int:
        q = select(func.count()).select_from(SearchLog)
        for c in conds:
            q = q.where(c)
        return (await db.execute(q)).scalar() or 0

    calls_24h = (
        await db.execute(
            select(func.coalesce(func.sum(SearchLog.calls_used), 0)).where(
                SearchLog.created_at >= since_24h
            )
        )
    ).scalar() or 0

    return {
        "last_search_at": last_search_at.isoformat() if last_search_at else None,
        "searches_last_hour": await _count(SearchLog.created_at >= since_1h),
        "searches_last_24h": await _count(SearchLog.created_at >= since_24h),
        "ok_last_24h": await _count(SearchLog.created_at >= since_24h, SearchLog.status == "ok"),
        "skipped_last_24h": await _count(SearchLog.created_at >= since_24h, SearchLog.status == "skipped"),
        "error_last_24h": await _count(SearchLog.created_at >= since_24h, SearchLog.status == "error"),
        "calls_last_24h": int(calls_24h),
    }
