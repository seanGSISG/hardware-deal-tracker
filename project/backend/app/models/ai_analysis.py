from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.listing import Listing


class AIAnalysis(Base):
    """LLM deal analysis for a listing (feature-006): grade, scam signal, specs."""

    __tablename__ = "ai_analyses"

    id: Mapped[int] = mapped_column(primary_key=True)
    listing_id: Mapped[int] = mapped_column(ForeignKey("listings.id"))
    tracked_item_id: Mapped[int | None] = mapped_column(ForeignKey("tracked_items.id", ondelete="CASCADE"))
    provider: Mapped[str] = mapped_column(String(30))
    model: Mapped[str] = mapped_column(String(120))
    deal_grade: Mapped[str | None] = mapped_column(String(40))
    reasoning: Mapped[str | None] = mapped_column(Text)
    scam_signal: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    scam_reasons: Mapped[list | None] = mapped_column(JSON)
    extracted_specs: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    listing: Mapped["Listing"] = relationship("Listing")
