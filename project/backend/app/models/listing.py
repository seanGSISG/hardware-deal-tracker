from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, Numeric, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.alert import Alert
    from app.models.listing_score import ListingScore
    from app.models.tracked_item import TrackedItem


class Listing(Base):
    __tablename__ = "listings"
    # Cross-source dedup key (feature-005): the same listing id can exist under
    # two sources (e.g. a TechMikeNY item appears in both its site and the eBay
    # feed), so uniqueness is on the (source, marketplace_id) pair.
    __table_args__ = (UniqueConstraint("source", "marketplace_id", name="uq_listings_source_marketplace_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    source: Mapped[str] = mapped_column(String(30), nullable=False, default="ebay", server_default="ebay")
    marketplace_id: Mapped[str] = mapped_column(String(100), nullable=False)
    tracked_item_id: Mapped[int | None] = mapped_column(ForeignKey("tracked_items.id", ondelete="CASCADE"))
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    normalized_title: Mapped[str | None] = mapped_column(String(500))
    price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    shipping: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    seller: Mapped[str] = mapped_column(String(200), nullable=False)
    seller_feedback: Mapped[int] = mapped_column(Integer, default=0)
    seller_positive_pct: Mapped[float] = mapped_column(Numeric(5, 2), default=100.0)
    condition: Mapped[str | None] = mapped_column(String(50))
    condition_id: Mapped[str | None] = mapped_column(String(20))
    category_id: Mapped[str | None] = mapped_column(String(20))
    url: Mapped[str] = mapped_column(String(2000), nullable=False)
    image_url: Mapped[str | None] = mapped_column(String(2000))
    is_auction: Mapped[bool] = mapped_column(Boolean, default=False)
    # Item origin (ISO-3166 alpha-2, e.g. "CN") + a derived China-origin flag for
    # the UI badge. Both populated from the eBay itemLocation.country at parse.
    item_country: Mapped[str | None] = mapped_column(String(2))
    is_china: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    quantity: Mapped[int] = mapped_column(Integer, default=1)
    buying_options: Mapped[list[str] | None] = mapped_column(JSON)
    listing_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    is_deduped: Mapped[bool] = mapped_column(Boolean, default=False)
    raw_data: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    tracked_item: Mapped["TrackedItem | None"] = relationship("TrackedItem", back_populates="listings")
    scores: Mapped[list["ListingScore"]] = relationship("ListingScore", back_populates="listing")
    alerts: Mapped[list["Alert"]] = relationship("Alert", back_populates="listing")
