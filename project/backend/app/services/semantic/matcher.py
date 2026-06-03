"""SemanticMatcher: optional pgvector-backed catalog matching (feature-006, ADR-006).

STRETCH / OPTIONAL. Suggests the best catalog (TrackedItem) for an unmatched or
ambiguous listing, and ranks "similar tracked items", using embedding cosine
similarity. The whole path is a no-op (returns None / empty) when
ENABLE_SEMANTIC_MATCHING is false, AI is disabled, or embeddings are
unavailable, and never raises into the poll path.

Ranking is implemented as a pure, dialect-independent function over in-memory
vectors so it is unit-testable on the sqlite suite without pgvector. On Postgres
the same correctness holds; a pgvector ``<=>`` ordering can be layered on later
as a query-side optimisation without changing this contract.
"""
from __future__ import annotations

import logging
import math
from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.listing import Listing
from app.models.tracked_item import TrackedItem
from app.services.ai.client import AIClient

logger = logging.getLogger(__name__)

Vector = Sequence[float]


def cosine_similarity(a: Vector, b: Vector) -> float:
    """Cosine similarity in [-1, 1]; 0.0 for any zero/empty/mismatched vector."""
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b, strict=False))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0.0 or nb == 0.0:
        return 0.0
    return dot / (na * nb)


def rank_by_similarity(
    query: Vector, candidates: list[tuple[object, Vector | None]]
) -> list[tuple[object, float]]:
    """Rank (key, embedding) candidates by cosine similarity to ``query``, desc.

    Candidates with no embedding are skipped. Pure function — no DB, no pgvector.
    """
    scored = [
        (key, cosine_similarity(query, emb))
        for key, emb in candidates
        if emb is not None
    ]
    scored.sort(key=lambda kv: kv[1], reverse=True)
    return scored


class SemanticMatcher:
    """Gated, graceful semantic matching over tracked-item embeddings."""

    def __init__(self, db: AsyncSession, ai: AIClient | None = None) -> None:
        self.db = db
        self.ai = ai or AIClient()

    @property
    def is_enabled(self) -> bool:
        """The feature only runs when explicitly enabled AND AI is usable."""
        return bool(settings.ENABLE_SEMANTIC_MATCHING) and self.ai.is_enabled

    async def _items_with_embeddings(self) -> list[TrackedItem]:
        rows = (
            await self.db.execute(
                select(TrackedItem).where(TrackedItem.embedding.is_not(None))
            )
        ).scalars().all()
        return list(rows)

    async def suggest_catalog_item(
        self, listing: Listing
    ) -> tuple[TrackedItem, float] | None:
        """Best-match (TrackedItem, score) for a listing, or None.

        No-op when disabled, when the listing title cannot be embedded, when no
        tracked item carries an embedding, or when the top score is below
        SEMANTIC_MIN_SIMILARITY. Never raises.
        """
        if not self.is_enabled:
            return None
        try:
            query = await self.ai.embed(listing.title or "")
            if not query:
                return None
            items = await self._items_with_embeddings()
            if not items:
                return None
            ranked = rank_by_similarity(
                query, [(item, item.embedding) for item in items]
            )
            if not ranked:
                return None
            best, score = ranked[0]
            if score < settings.SEMANTIC_MIN_SIMILARITY:
                return None
            return best, score  # type: ignore[return-value]
        except Exception:
            logger.exception("semantic suggest_catalog_item failed; degrading to None")
            return None

    async def similar_items(
        self, tracked_item: TrackedItem, top_n: int | None = None
    ) -> list[tuple[TrackedItem, float]]:
        """Top-N tracked items most similar to ``tracked_item`` by embedding.

        Empty list when disabled, when the anchor has no embedding, or on any
        error. The anchor item is excluded from its own results. Never raises.
        """
        if not self.is_enabled:
            return []
        try:
            anchor = tracked_item.embedding
            if not anchor:
                return []
            limit = top_n or settings.SEMANTIC_SIMILAR_TOP_N
            items = [
                item
                for item in await self._items_with_embeddings()
                if item.id != tracked_item.id
            ]
            ranked = rank_by_similarity(anchor, [(item, item.embedding) for item in items])
            return [(item, score) for item, score in ranked[:limit]]  # type: ignore[misc]
        except Exception:
            logger.exception("semantic similar_items failed; degrading to empty")
            return []

    async def embed_and_store_items(self) -> int:
        """Best-effort: embed tracked items missing an embedding and store them.

        No-op (returns 0) when disabled or when embeddings are unavailable.
        Returns the number of items updated. Never raises.
        """
        if not self.is_enabled:
            return 0
        try:
            rows = (
                await self.db.execute(
                    select(TrackedItem).where(TrackedItem.embedding.is_(None))
                )
            ).scalars().all()
            items = list(rows)
            if not items:
                return 0
            # Embed from the catalog name + keywords (the most descriptive text).
            texts = [f"{i.name} {i.keywords}".strip() for i in items]
            vectors = await self.ai.embed_batch(texts)
            if not vectors or len(vectors) != len(items):
                return 0
            updated = 0
            for item, vec in zip(items, vectors, strict=False):
                if vec:
                    item.embedding = list(vec)
                    updated += 1
            await self.db.commit()
            return updated
        except Exception:
            logger.exception("semantic embed_and_store_items failed; degrading to no-op")
            await self.db.rollback()
            return 0
