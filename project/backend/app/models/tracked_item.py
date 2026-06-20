from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Integer, Numeric, String, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.config import settings
from app.db.base import Base
from app.db.vector_type import EmbeddingVector

if TYPE_CHECKING:
    from app.models.listing import Listing
    from app.models.price_history import PriceHistory


class TrackedItem(Base):
    __tablename__ = "tracked_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    keywords: Mapped[str] = mapped_column(String(1000), nullable=False)
    sku: Mapped[str | None] = mapped_column(String(100))
    mpn: Mapped[str | None] = mapped_column(String(100))
    category_id: Mapped[str | None] = mapped_column(String(20))
    marketplace: Mapped[str] = mapped_column(String(20), default="ebay", server_default="ebay")
    target_price: Mapped[float | None] = mapped_column(Numeric(10, 2))
    alert_threshold: Mapped[float] = mapped_column(Numeric(5, 2), default=0.20, server_default=text("0.20"))
    min_deal_score: Mapped[int] = mapped_column(Integer, default=50, server_default=text("50"))
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, server_default=text("true"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    last_searched: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    search_interval: Mapped[int] = mapped_column(Integer, default=600, server_default=text("600"))
    scam_floor: Mapped[float | None] = mapped_column(Numeric(10, 2))
    benchmark_median: Mapped[float | None] = mapped_column(Numeric(10, 2))
    # Optional PCPartPicker product mapping (feature-005): set for the ~10-12
    # consumer/prosumer catalog items PCPartPicker can benchmark; null otherwise.
    pcpp_product_id: Mapped[str | None] = mapped_column(String(100))
    notes: Mapped[str | None] = mapped_column(String(500))
    # Optional catalog embedding for semantic matching (feature-006, ADR-006).
    # Nullable + dialect-guarded: a real pgvector column on Postgres, JSON on
    # sqlite. Populated best-effort only when ENABLE_SEMANTIC_MATCHING + AI are
    # on; null otherwise, so the column is inert for the core app.
    embedding: Mapped[list[float] | None] = mapped_column(
        EmbeddingVector(settings.SEMANTIC_EMBEDDING_DIM), nullable=True
    )

    # passive_deletes=True: defer child deletion to the DB-level ON DELETE CASCADE
    # (the 7 FKs into tracked_items) instead of SQLAlchemy trying to NULL the child
    # FK on parent delete — price_history.tracked_item_id is NOT NULL, so the ORM's
    # default NULL-out would error. cascade lets a delete of the parent propagate.
    listings: Mapped[list["Listing"]] = relationship(
        "Listing", back_populates="tracked_item",
        cascade="all, delete-orphan", passive_deletes=True,
    )
    price_history: Mapped[list["PriceHistory"]] = relationship(
        "PriceHistory", back_populates="tracked_item",
        cascade="all, delete-orphan", passive_deletes=True,
    )

    @property
    def priority_tier(self) -> str:
        if self.search_interval <= 360:
            return "P0"
        elif self.search_interval <= 600:
            return "P1"
        elif self.search_interval <= 1200:
            return "P2"
        return "P3"
