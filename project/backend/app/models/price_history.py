from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Numeric, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.tracked_item import TrackedItem


class PriceHistory(Base):
    __tablename__ = "price_history"

    id: Mapped[int] = mapped_column(primary_key=True)
    listing_id: Mapped[int] = mapped_column(ForeignKey("listings.id"))
    tracked_item_id: Mapped[int] = mapped_column(ForeignKey("tracked_items.id", ondelete="CASCADE"))
    observed_price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    shipping: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    total_price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    tracked_item: Mapped["TrackedItem"] = relationship("TrackedItem", back_populates="price_history")
