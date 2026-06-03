from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.notification_setting import NotificationSetting
from app.models.user import User
from app.schemas.settings import NotificationSettingsUpdate

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("/notifications")
async def get_settings(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    result = await db.execute(select(NotificationSetting).where(NotificationSetting.user_id == user.id))
    settings = result.scalar_one_or_none()
    if not settings:
        settings = NotificationSetting(user_id=user.id)
        db.add(settings)
        await db.flush()
        await db.refresh(settings)
    return settings


@router.put("/notifications")
async def update_settings(
    data: NotificationSettingsUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    result = await db.execute(select(NotificationSetting).where(NotificationSetting.user_id == user.id))
    settings = result.scalar_one_or_none()
    if not settings:
        # Upsert: lazily create the row (GET already does this) instead of 404ing.
        settings = NotificationSetting(user_id=user.id)
        db.add(settings)

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(settings, field, value)
    await db.flush()
    await db.refresh(settings)
    return settings
