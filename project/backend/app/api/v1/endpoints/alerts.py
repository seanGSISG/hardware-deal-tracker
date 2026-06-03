
from fastapi import APIRouter, Depends, Query
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.alert import Alert
from app.models.user import User

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get("")
async def list_alerts(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    channel: str | None = None,
    sent: bool | None = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    query = select(Alert)
    if channel:
        query = query.where(Alert.channel == channel)
    if sent is not None:
        query = query.where(Alert.was_sent == sent)

    count_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = count_result.scalar()

    query = query.offset((page - 1) * per_page).limit(per_page).order_by(desc(Alert.created_at))
    result = await db.execute(query)
    alerts = result.scalars().all()

    return {"alerts": alerts, "total": total, "page": page, "per_page": per_page}


@router.put("/{alert_id}/read")
async def mark_read(
    alert_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    from datetime import datetime
    result = await db.execute(select(Alert).where(Alert.id == alert_id))
    alert = result.scalar_one_or_none()
    if alert:
        alert.was_sent = True
        alert.sent_at = datetime.utcnow()
    return alert
