"""Intermediate shapes for the community-signal leads pipeline (feature-007).

These are plain dataclasses (NOT SQLAlchemy models / NormalizedListing) so the
community path stays clearly separate from the scored-listing pipeline. A
``CommunityPost`` is the raw fetched post; a ``CommunityLead`` is the structured
result of AI free-text extraction that (after sold/traded filtering + dedup) is
persisted into the ``community_signal_leads`` table.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

# Lead status vocabulary the extractor must map free text onto.
LEAD_STATUSES = ("for-sale", "sold", "traded", "pending", "unknown")

# Statuses that mean the deal is gone — filtered out before persistence.
STALE_STATUSES = frozenset({"sold", "traded", "pending"})


@dataclass
class CommunityPost:
    """A raw community post fetched from a source (e.g. Reddit r/homelabsales)."""

    source: str
    source_post_id: str
    title: str
    body: str
    url: str
    author: str | None = None
    created_at: datetime | None = None
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass
class CommunityLead:
    """A structured lead extracted from a CommunityPost's free text.

    ``catalog_item_id`` is set only when the parsed model matches a tracked
    catalog item; otherwise None. ``status`` is one of LEAD_STATUSES.
    """

    source: str
    source_post_id: str
    title: str
    url: str
    author: str | None = None
    catalog_item_id: int | None = None
    model: str | None = None
    price: float | None = None
    condition: str | None = None
    location: str | None = None
    status: str = "unknown"
    confidence: float | None = None
    ai_reason: str | None = None
    posted_at: datetime | None = None
    raw: dict[str, Any] = field(default_factory=dict)

    @property
    def is_stale(self) -> bool:
        """True when the extracted status indicates the deal is gone."""
        return (self.status or "unknown").strip().lower() in STALE_STATUSES
