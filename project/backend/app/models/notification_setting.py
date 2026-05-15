from datetime import datetime
from typing import Optional
from sqlalchemy import String, Boolean, DateTime, Integer, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class NotificationSetting(Base):
    __tablename__ = "notification_settings"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)
    telegram_chat_id: Mapped[Optional[str]] = mapped_column(String(100))
    telegram_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    email_address: Mapped[Optional[str]] = mapped_column(String(255))
    email_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    email_digest_mode: Mapped[str] = mapped_column(String(20), default="daily")
    telegram_min_score: Mapped[int] = mapped_column(Integer, default=70)
    email_min_score: Mapped[int] = mapped_column(Integer, default=50)
    mute_until: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user: Mapped["User"] = relationship("User")
