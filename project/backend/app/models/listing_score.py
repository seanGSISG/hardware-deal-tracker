from datetime import datetime
from typing import Optional
from sqlalchemy import String, Numeric, Integer, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class ListingScore(Base):
    __tablename__ = "listing_scores"

    id: Mapped[int] = mapped_column(primary_key=True)
    listing_id: Mapped[int] = mapped_column(ForeignKey("listings.id"))
    tracked_item_id: Mapped[int] = mapped_column(ForeignKey("tracked_items.id"))
    overall_score: Mapped[int] = mapped_column(Integer, nullable=False)
    deal_score: Mapped[int] = mapped_column(Integer, nullable=False)
    confidence: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    classification: Mapped[str] = mapped_column(String(50))
    price_zscore: Mapped[Optional[float]] = mapped_column(Numeric(8, 4))
    vs_median_pct: Mapped[Optional[float]] = mapped_column(Numeric(8, 4))
    vs_lowest_pct: Mapped[Optional[float]] = mapped_column(Numeric(8, 4))
    est_fair_value: Mapped[Optional[float]] = mapped_column(Numeric(10, 2))
    scam_flag: Mapped[Optional[str]] = mapped_column(String(200))
    scored_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    listing: Mapped["Listing"] = relationship("Listing", back_populates="scores")
