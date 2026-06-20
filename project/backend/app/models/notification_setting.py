from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.user import User


class NotificationSetting(Base):
    __tablename__ = "notification_settings"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)
    telegram_chat_id: Mapped[str | None] = mapped_column(String(100))
    telegram_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    email_address: Mapped[str | None] = mapped_column(String(255))
    email_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    email_digest_mode: Mapped[str] = mapped_column(String(20), default="daily")
    telegram_min_score: Mapped[int] = mapped_column(Integer, default=70)
    email_min_score: Mapped[int] = mapped_column(Integer, default=50)
    # ntfy (self-hosted push). Opt-in; topic falls back to settings.NTFY_TOPIC.
    ntfy_enabled: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    ntfy_topic: Mapped[str | None] = mapped_column(String(100))
    ntfy_min_score: Mapped[int] = mapped_column(Integer, default=70, server_default="70")
    mute_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    user: Mapped["User"] = relationship("User")
