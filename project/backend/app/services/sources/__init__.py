"""Multi-source ingestion adapters (feature-005).

Every external price/listing source is wrapped in a `SourceAdapter` that
normalizes its responses to the shared `NormalizedListing` shape, so the poller
can fan out across sources without knowing each source's transport.

See `docs/ADDING_A_SOURCE_ADAPTER.md` for how to add a new adapter.
"""
from app.services.sources.base import NormalizedListing, SourceAdapter

__all__ = ["NormalizedListing", "SourceAdapter"]
