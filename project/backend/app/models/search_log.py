from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class SearchLog(Base):
    """Audit row for every search performed against a source.

    One row is written each time the poller searches a single tracked item
    (whether the search executed, was skipped for budget, or errored). This is
    the durable backing store for the dashboard Activity page — the poll result
    dicts and Prometheus counters are otherwise ephemeral.

    `tracked_item_id` is SET NULL (not CASCADE) on item delete and `item_name`
    is denormalised so the activity history survives the item being removed.
    """

    __tablename__ = "search_log"

    id: Mapped[int] = mapped_column(primary_key=True)
    tracked_item_id: Mapped[int | None] = mapped_column(
        ForeignKey("tracked_items.id", ondelete="SET NULL"), nullable=True, index=True
    )
    # Denormalised so the log line is still readable after the item is deleted.
    item_name: Mapped[str] = mapped_column(String(300), nullable=False)
    source: Mapped[str] = mapped_column(String(50), nullable=False, default="ebay")
    # "ok" | "skipped" | "error"
    status: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    priority: Mapped[str | None] = mapped_column(String(10))

    listings_found: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    new_listings: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    duplicates: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    # eBay calls this search consumed (1 for an executed eBay search, 0 if skipped).
    calls_used: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    duration_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    # Skip reason or error message; null on a clean search.
    detail: Mapped[str | None] = mapped_column(String(500))

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
