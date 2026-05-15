from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, Numeric, Boolean, DateTime, Integer, JSON, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class Listing(Base):
    __tablename__ = "listings"

    id: Mapped[int] = mapped_column(primary_key=True)
    marketplace_id: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    tracked_item_id: Mapped[Optional[int]] = mapped_column(ForeignKey("tracked_items.id"))
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    normalized_title: Mapped[Optional[str]] = mapped_column(String(500))
    price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    shipping: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    seller: Mapped[str] = mapped_column(String(200), nullable=False)
    seller_feedback: Mapped[int] = mapped_column(Integer, default=0)
    seller_positive_pct: Mapped[float] = mapped_column(Numeric(5, 2), default=100.0)
    condition: Mapped[Optional[str]] = mapped_column(String(50))
    condition_id: Mapped[Optional[str]] = mapped_column(String(20))
    category_id: Mapped[Optional[str]] = mapped_column(String(20))
    url: Mapped[str] = mapped_column(String(2000), nullable=False)
    image_url: Mapped[Optional[str]] = mapped_column(String(2000))
    is_auction: Mapped[bool] = mapped_column(Boolean, default=False)
    quantity: Mapped[int] = mapped_column(Integer, default=1)
    buying_options: Mapped[Optional[List[str]]] = mapped_column(JSON)
    listing_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    is_deduped: Mapped[bool] = mapped_column(Boolean, default=False)
    raw_data: Mapped[Optional[dict]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    tracked_item: Mapped[Optional["TrackedItem"]] = relationship("TrackedItem", back_populates="listings")
    scores: Mapped[list["ListingScore"]] = relationship("ListingScore", back_populates="listing")
    alerts: Mapped[list["Alert"]] = relationship("Alert", back_populates="listing")
