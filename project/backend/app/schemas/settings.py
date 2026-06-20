from datetime import datetime

from pydantic import BaseModel


class NotificationSettingsResponse(BaseModel):
    id: int
    user_id: int
    telegram_chat_id: str | None = None
    telegram_enabled: bool = True
    email_address: str | None = None
    email_enabled: bool = True
    email_digest_mode: str = "daily"
    telegram_min_score: int = 70
    email_min_score: int = 50
    ntfy_enabled: bool = False
    ntfy_topic: str | None = None
    ntfy_min_score: int = 70
    mute_until: datetime | None = None

    class Config:
        from_attributes = True


class NotificationSettingsUpdate(BaseModel):
    telegram_chat_id: str | None = None
    telegram_enabled: bool | None = None
    email_address: str | None = None
    email_enabled: bool | None = None
    email_digest_mode: str | None = None
    telegram_min_score: int | None = None
    email_min_score: int | None = None
    ntfy_enabled: bool | None = None
    ntfy_topic: str | None = None
    ntfy_min_score: int | None = None
    mute_until: datetime | None = None
