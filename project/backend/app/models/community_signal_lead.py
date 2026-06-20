from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    JSON,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.tracked_item import TrackedItem


class CommunitySignalLead(Base):
    """A structured lead extracted from an unstructured community post (feature-007).

    This is a SEPARATE surface from the scored-listing pipeline (ADR-007): leads
    are NEVER routed through DealScoringEngine / ListingScore / PriceHistory /
    NotificationDispatcher. Dedup is enforced by the unique (source,
    source_post_id) constraint — the leads analog of the listing
    (source, source_listing_id) pattern.
    """

    __tablename__ = "community_signal_leads"
    __table_args__ = (
        UniqueConstraint(
            "source", "source_post_id", name="uq_community_signal_leads_source_post"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    source: Mapped[str] = mapped_column(String(40), nullable=False)
    source_post_id: Mapped[str] = mapped_column(String(100), nullable=False)
    catalog_item_id: Mapped[int | None] = mapped_column(ForeignKey("tracked_items.id", ondelete="CASCADE"))

    title: Mapped[str] = mapped_column(String(500), nullable=False)
    url: Mapped[str] = mapped_column(String(2000), nullable=False)
    author: Mapped[str | None] = mapped_column(String(200))

    model: Mapped[str | None] = mapped_column(String(255))
    price: Mapped[float | None] = mapped_column(Numeric(10, 2))
    condition: Mapped[str | None] = mapped_column(String(80))
    location: Mapped[str | None] = mapped_column(String(120))
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="unknown")
    confidence: Mapped[float | None] = mapped_column(Numeric(4, 3))
    ai_reason: Mapped[str | None] = mapped_column(String(500))

    raw_payload: Mapped[dict | None] = mapped_column(JSON)
    posted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    ingested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    catalog_item: Mapped["TrackedItem | None"] = relationship("TrackedItem")
