from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class NotificationSettingsResponse(BaseModel):
    id: int
    user_id: int
    telegram_chat_id: Optional[str] = None
    telegram_enabled: bool = True
    email_address: Optional[str] = None
    email_enabled: bool = True
    email_digest_mode: str = "daily"
    telegram_min_score: int = 70
    email_min_score: int = 50
    mute_until: Optional[datetime] = None

    class Config:
        from_attributes = True


class NotificationSettingsUpdate(BaseModel):
    telegram_chat_id: Optional[str] = None
    telegram_enabled: Optional[bool] = None
    email_address: Optional[str] = None
    email_enabled: Optional[bool] = None
    email_digest_mode: Optional[str] = None
    telegram_min_score: Optional[int] = None
    email_min_score: Optional[int] = None
    mute_until: Optional[datetime] = None
