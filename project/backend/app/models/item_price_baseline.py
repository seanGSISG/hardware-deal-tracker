from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.tracked_item import TrackedItem


class ItemPriceBaseline(Base):
    """Rolling per-item market-history baseline snapshot (feature-001, ADR-001).

    Exactly one *current* row per tracked item (unique ``tracked_item_id``),
    refreshed daily by ``ScoringBaselineService``. Holds the Tukey-trimmed
    median/IQR/stats over the rolling lookback window plus the 30d trend signal,
    so the poll path can read a cheap snapshot instead of recomputing per tick.

    ``source`` records where the snapshot came from:
      * ``sold_comps``     — real eBay sold/completed comps (future, gated)
      * ``price_history``  — accumulated PriceHistory points (today's path)
      * ``benchmark``      — insufficient comps; scoring degrades to
                             ``TrackedItem.benchmark_median``.
    """

    __tablename__ = "item_price_baselines"

    id: Mapped[int] = mapped_column(primary_key=True)
    tracked_item_id: Mapped[int] = mapped_column(
        ForeignKey("tracked_items.id"), unique=True, nullable=False
    )

    median_price: Mapped[float | None] = mapped_column(Numeric(10, 2))
    avg_price: Mapped[float | None] = mapped_column(Numeric(10, 2))
    std_dev: Mapped[float | None] = mapped_column(Numeric(10, 2))
    min_price: Mapped[float | None] = mapped_column(Numeric(10, 2))
    q1: Mapped[float | None] = mapped_column(Numeric(10, 2))
    q3: Mapped[float | None] = mapped_column(Numeric(10, 2))
    data_points: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    lookback_days: Mapped[int | None] = mapped_column(Integer)

    trend_direction: Mapped[str | None] = mapped_column(String(20))
    trend_slope_pct: Mapped[float | None] = mapped_column(Numeric(8, 4))

    source: Mapped[str] = mapped_column(String(20), nullable=False, default="benchmark")
    computed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    tracked_item: Mapped["TrackedItem"] = relationship("TrackedItem")
