from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.models.notification_setting import NotificationSetting
from app.schemas.settings import NotificationSettingsResponse, NotificationSettingsUpdate

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
        raise HTTPException(status_code=404, detail="Settings not found")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(settings, field, value)
    await db.flush()
    await db.refresh(settings)
    return settings
