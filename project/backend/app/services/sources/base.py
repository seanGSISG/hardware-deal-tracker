"""SourceAdapter contract + normalized listing shape (feature-005, ADR-003).

`NormalizedListing` is the single record every ingestion source maps to. The
poller dedups on `(source, source_listing_id)` and persists each normalized
listing as a `Listing` row, so adding a new source never touches the
scheduler / scoring / notification core.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class NormalizedListing:
    """A source-agnostic listing record.

    Fields match design_doc's NormalizedListing plus the cross-source dedup key
    (`source`, `source_listing_id`) and the catalog linkage used by scoring.
    """

    source: str
    source_listing_id: str
    title: str
    url: str
    price: float
    currency: str = "USD"
    shipping: float = 0.0
    condition: str | None = None
    availability: str | None = None
    seller: str | None = None
    catalog_item_id: int | None = None
    raw_payload: dict[str, Any] = field(default_factory=dict)
    fetched_at: datetime = field(default_factory=datetime.utcnow)

    @property
    def total(self) -> float:
        """Price including shipping — the figure scoring/comparison uses."""
        return float(self.price) + float(self.shipping or 0.0)


class SourceAdapter(ABC):
    """Common interface for every listing/price source.

    Concrete adapters set a class-level `source` identity and implement
    `search(catalog_item)`, returning normalized listings. They own their
    transport and per-source rate limits / ToS handling.
    """

    #: Stable per-source identity, e.g. "ebay", "pcpartpicker", "techmikeny".
    source: str = ""

    @abstractmethod
    async def search(self, catalog_item) -> list[NormalizedListing]:
        """Return normalized listings for a catalog (tracked) item."""
        raise NotImplementedError
