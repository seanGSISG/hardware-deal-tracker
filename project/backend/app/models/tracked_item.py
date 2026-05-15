from datetime import datetime
from typing import Optional
from sqlalchemy import String, Numeric, Boolean, DateTime, Integer, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class TrackedItem(Base):
    __tablename__ = "tracked_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    keywords: Mapped[str] = mapped_column(String(1000), nullable=False)
    sku: Mapped[Optional[str]] = mapped_column(String(100))
    mpn: Mapped[Optional[str]] = mapped_column(String(100))
    category_id: Mapped[Optional[str]] = mapped_column(String(20))
    marketplace: Mapped[str] = mapped_column(String(20), default="ebay")
    target_price: Mapped[Optional[float]] = mapped_column(Numeric(10, 2))
    alert_threshold: Mapped[float] = mapped_column(Numeric(5, 2), default=0.20)
    min_deal_score: Mapped[int] = mapped_column(Integer, default=50)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    last_searched: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    search_interval: Mapped[int] = mapped_column(Integer, default=600)
    scam_floor: Mapped[Optional[float]] = mapped_column(Numeric(10, 2))
    benchmark_median: Mapped[Optional[float]] = mapped_column(Numeric(10, 2))
    notes: Mapped[Optional[str]] = mapped_column(String(500))

    listings: Mapped[list["Listing"]] = relationship("Listing", back_populates="tracked_item")
    price_history: Mapped[list["PriceHistory"]] = relationship("PriceHistory", back_populates="tracked_item")

    @property
    def priority_tier(self) -> str:
        if self.search_interval <= 360:
            return "P0"
        elif self.search_interval <= 600:
            return "P1"
        elif self.search_interval <= 1200:
            return "P2"
        return "P3"
