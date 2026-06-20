from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.listing import Listing


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(primary_key=True)
    listing_id: Mapped[int] = mapped_column(ForeignKey("listings.id"))
    tracked_item_id: Mapped[int] = mapped_column(ForeignKey("tracked_items.id", ondelete="CASCADE"))
    score_id: Mapped[int | None] = mapped_column(ForeignKey("listing_scores.id"))
    channel: Mapped[str] = mapped_column(String(20), nullable=False)
    alert_type: Mapped[str] = mapped_column(String(20), nullable=False)
    was_sent: Mapped[bool] = mapped_column(Boolean, default=False)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    template_used: Mapped[str | None] = mapped_column(String(50))
    telegram_msg_id: Mapped[str | None] = mapped_column(String(100))
    error_message: Mapped[str | None] = mapped_column(String(1000))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    listing: Mapped["Listing"] = relationship("Listing", back_populates="alerts")
