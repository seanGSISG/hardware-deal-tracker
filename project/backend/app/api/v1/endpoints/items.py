from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, case
from typing import Optional
from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.models.tracked_item import TrackedItem
from app.models.listing import Listing
from app.schemas.tracked_item import (
    TrackedItemCreate, TrackedItemUpdate, TrackedItemResponse, TrackedItemStats
)


def _serialize_item(item: TrackedItem, latest_image_url: Optional[str]) -> dict:
    data = {k: v for k, v in item.__dict__.items() if not k.startswith("_")}
    data["priority_tier"] = item.priority_tier
    data["latest_image_url"] = latest_image_url
    return data

router = APIRouter(prefix="/items", tags=["items"])


@router.get("/stats", response_model=TrackedItemStats)
async def get_item_stats(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    result = await db.execute(
        select(
            func.count(TrackedItem.id).label("total"),
            func.sum(case((TrackedItem.is_enabled == True, 1), else_=0)).label("enabled"),
            func.sum(case((TrackedItem.search_interval <= 360, 1), else_=0)).label("p0"),
            func.sum(case((TrackedItem.search_interval.between(361, 600), 1), else_=0)).label("p1"),
            func.sum(case((TrackedItem.search_interval.between(601, 1200), 1), else_=0)).label("p2"),
            func.sum(case((TrackedItem.search_interval > 1200, 1), else_=0)).label("p3"),
        )
    )
    row = result.first()
    p0_calls = (row.p0 or 0) * 288
    p1_calls = (row.p1 or 0) * 144
    p2_calls = (row.p2 or 0) * 72
    p3_calls = (row.p3 or 0) * 48
    return TrackedItemStats(
        total_items=row.total or 0,
        enabled_items=row.enabled or 0,
        p0_count=row.p0 or 0,
        p1_count=row.p1 or 0,
        p2_count=row.p2 or 0,
        p3_count=row.p3 or 0,
        estimated_daily_calls=p0_calls + p1_calls + p2_calls + p3_calls,
    )


@router.get("")
async def list_items(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    enabled: Optional[bool] = None,
    priority: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    latest_image_subq = (
        select(Listing.image_url)
        .where(Listing.tracked_item_id == TrackedItem.id)
        .where(Listing.image_url.is_not(None))
        .order_by(Listing.listing_date.desc(), Listing.created_at.desc())
        .limit(1)
        .correlate(TrackedItem)
        .scalar_subquery()
    )

    query = select(TrackedItem, latest_image_subq.label("latest_image_url"))
    if enabled is not None:
        query = query.where(TrackedItem.is_enabled == enabled)
    if priority == "P0":
        query = query.where(TrackedItem.search_interval <= 360)
    elif priority == "P1":
        query = query.where(TrackedItem.search_interval.between(361, 600))
    elif priority == "P2":
        query = query.where(TrackedItem.search_interval.between(601, 1200))
    elif priority == "P3":
        query = query.where(TrackedItem.search_interval > 1200)

    count_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = count_result.scalar()

    query = query.offset((page - 1) * per_page).limit(per_page).order_by(TrackedItem.created_at.desc())
    result = await db.execute(query)
    rows = result.all()
    items = [_serialize_item(item, latest_image_url) for item, latest_image_url in rows]

    return {"items": items, "total": total, "page": page, "per_page": per_page}


@router.post("", response_model=TrackedItemResponse)
async def create_item(data: TrackedItemCreate, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    item = TrackedItem(**data.model_dump())
    db.add(item)
    await db.flush()
    await db.refresh(item)
    return item


@router.post("/bulk-update")
async def bulk_update(data: dict, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    ids = data.get("ids", [])
    action = data.get("action", "")
    value = data.get("value")
    if not ids:
        raise HTTPException(status_code=400, detail="No item IDs provided")

    result = await db.execute(select(TrackedItem).where(TrackedItem.id.in_(ids)))
    items = result.scalars().all()
    updated = 0
    for item in items:
        if action == "enable":
            item.is_enabled = True
        elif action == "disable":
            item.is_enabled = False
        elif action == "set_interval" and value:
            item.search_interval = int(value)
        elif action == "delete":
            await db.delete(item)
        updated += 1
    await db.flush()
    return {"updated": updated, "action": action}


@router.get("/{item_id}", response_model=TrackedItemResponse)
async def get_item(item_id: int, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    latest_image_subq = (
        select(Listing.image_url)
        .where(Listing.tracked_item_id == TrackedItem.id)
        .where(Listing.image_url.is_not(None))
        .order_by(Listing.listing_date.desc(), Listing.created_at.desc())
        .limit(1)
        .correlate(TrackedItem)
        .scalar_subquery()
    )
    result = await db.execute(
        select(TrackedItem, latest_image_subq.label("latest_image_url"))
        .where(TrackedItem.id == item_id)
    )
    row = result.first()
    if not row:
        raise HTTPException(status_code=404, detail="Item not found")
    item, latest_image_url = row
    return _serialize_item(item, latest_image_url)


@router.put("/{item_id}", response_model=TrackedItemResponse)
async def update_item(item_id: int, data: TrackedItemUpdate, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    result = await db.execute(select(TrackedItem).where(TrackedItem.id == item_id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(item, field, value)
    await db.flush()
    await db.refresh(item)
    return item


@router.delete("/{item_id}")
async def delete_item(item_id: int, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    result = await db.execute(select(TrackedItem).where(TrackedItem.id == item_id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    await db.delete(item)
    return {"detail": "Item deleted"}


@router.put("/{item_id}/toggle")
async def toggle_item(item_id: int, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    result = await db.execute(select(TrackedItem).where(TrackedItem.id == item_id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    item.is_enabled = not item.is_enabled
    await db.flush()
    return {"id": item.id, "is_enabled": item.is_enabled}
