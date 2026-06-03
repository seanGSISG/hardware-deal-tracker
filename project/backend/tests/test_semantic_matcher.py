"""story-3 (feature-006): SemanticMatcher cosine-similarity catalog suggestion.

Ranking is a pure function over in-memory vectors so it runs on sqlite without
pgvector. The embedding client is mocked; embeddings live in the dialect-guarded
JSON column on sqlite. Everything is a no-op when the feature/AI is off.
"""
import pytest_asyncio

from app.core.config import settings
from app.models.listing import Listing
from app.models.tracked_item import TrackedItem
from app.services.ai.client import AIClient
from app.services.semantic.matcher import SemanticMatcher, cosine_similarity, rank_by_similarity

# --- pure ranking ----------------------------------------------------------

def test_cosine_similarity_identical():
    assert cosine_similarity([1.0, 0.0], [1.0, 0.0]) == 1.0


def test_cosine_similarity_orthogonal():
    assert cosine_similarity([1.0, 0.0], [0.0, 1.0]) == 0.0


def test_cosine_similarity_zero_vector_is_safe():
    assert cosine_similarity([0.0, 0.0], [1.0, 1.0]) == 0.0


def test_rank_by_similarity_orders_descending():
    query = [1.0, 0.0]
    candidates = [
        ("a", [0.0, 1.0]),   # orthogonal -> 0.0
        ("b", [1.0, 0.0]),   # identical -> 1.0
        ("c", [0.9, 0.1]),   # close -> high
    ]
    ranked = rank_by_similarity(query, candidates)
    assert [key for key, _ in ranked] == ["b", "c", "a"]
    assert ranked[0][1] == 1.0


def test_rank_skips_missing_embeddings():
    ranked = rank_by_similarity([1.0, 0.0], [("a", None), ("b", [1.0, 0.0])])
    assert [k for k, _ in ranked] == ["b"]


# --- service: gating -------------------------------------------------------

class _FakeAI(AIClient):
    def __init__(self, vector):
        self._vector = vector

    @property
    def is_enabled(self):  # type: ignore[override]
        return True

    async def embed(self, text):  # type: ignore[override]
        return self._vector

    async def embed_batch(self, texts):  # type: ignore[override]
        return [self._vector for _ in texts]


@pytest_asyncio.fixture
async def seeded(db):
    items = [
        TrackedItem(name="EPYC 7763", keywords="epyc 7763", embedding=[1.0, 0.0]),
        TrackedItem(name="RTX A5000", keywords="rtx a5000", embedding=[0.0, 1.0]),
        TrackedItem(name="EPYC 7713", keywords="epyc 7713", embedding=[0.9, 0.1]),
    ]
    db.add_all(items)
    await db.commit()
    return items


async def test_suggest_noop_when_feature_disabled(monkeypatch, db, seeded):
    monkeypatch.setattr(settings, "ENABLE_SEMANTIC_MATCHING", False)
    monkeypatch.setattr(settings, "AI_ENABLED", True)
    matcher = SemanticMatcher(db, ai=_FakeAI([1.0, 0.0]))
    listing = Listing(marketplace_id="x", title="AMD EPYC 7763", price=1000, seller="s", url="http://x")
    assert await matcher.suggest_catalog_item(listing) is None


async def test_suggest_noop_when_ai_disabled(monkeypatch, db, seeded):
    monkeypatch.setattr(settings, "ENABLE_SEMANTIC_MATCHING", True)
    monkeypatch.setattr(settings, "AI_ENABLED", False)
    # Use the REAL AIClient here so the AI-disabled gate is exercised (a fake
    # that forces is_enabled would defeat the point of this test).
    matcher = SemanticMatcher(db, ai=AIClient())
    listing = Listing(marketplace_id="x", title="AMD EPYC 7763", price=1000, seller="s", url="http://x")
    assert await matcher.suggest_catalog_item(listing) is None


async def test_suggest_returns_best_match(monkeypatch, db, seeded):
    monkeypatch.setattr(settings, "ENABLE_SEMANTIC_MATCHING", True)
    monkeypatch.setattr(settings, "AI_ENABLED", True)
    monkeypatch.setattr(settings, "SEMANTIC_MIN_SIMILARITY", 0.5)
    matcher = SemanticMatcher(db, ai=_FakeAI([1.0, 0.0]))
    listing = Listing(marketplace_id="x", title="AMD EPYC 7763", price=1000, seller="s", url="http://x")
    result = await matcher.suggest_catalog_item(listing)
    assert result is not None
    item, score = result
    assert item.name == "EPYC 7763"
    assert score == 1.0


async def test_suggest_respects_min_similarity(monkeypatch, db, seeded):
    monkeypatch.setattr(settings, "ENABLE_SEMANTIC_MATCHING", True)
    monkeypatch.setattr(settings, "AI_ENABLED", True)
    monkeypatch.setattr(settings, "SEMANTIC_MIN_SIMILARITY", 0.99)
    # Query orthogonal-ish to everything strong -> below threshold.
    matcher = SemanticMatcher(db, ai=_FakeAI([0.2, 0.2]))
    listing = Listing(marketplace_id="x", title="mystery", price=1, seller="s", url="http://x")
    assert await matcher.suggest_catalog_item(listing) is None


async def test_suggest_none_when_embed_unavailable(monkeypatch, db, seeded):
    monkeypatch.setattr(settings, "ENABLE_SEMANTIC_MATCHING", True)
    monkeypatch.setattr(settings, "AI_ENABLED", True)
    matcher = SemanticMatcher(db, ai=_FakeAI(None))  # embed() yields None
    listing = Listing(marketplace_id="x", title="AMD EPYC 7763", price=1, seller="s", url="http://x")
    assert await matcher.suggest_catalog_item(listing) is None


async def test_suggest_never_raises(monkeypatch, db):
    """Any internal failure degrades to None, never propagates into the poll path."""
    monkeypatch.setattr(settings, "ENABLE_SEMANTIC_MATCHING", True)
    monkeypatch.setattr(settings, "AI_ENABLED", True)

    class _BoomAI(AIClient):
        @property
        def is_enabled(self):  # type: ignore[override]
            return True

        async def embed(self, text):  # type: ignore[override]
            raise RuntimeError("boom")

    matcher = SemanticMatcher(db, ai=_BoomAI())
    listing = Listing(marketplace_id="x", title="x", price=1, seller="s", url="http://x")
    assert await matcher.suggest_catalog_item(listing) is None


# --- embed-and-store helper ------------------------------------------------

async def test_embed_and_store_noop_when_disabled(monkeypatch, db):
    monkeypatch.setattr(settings, "ENABLE_SEMANTIC_MATCHING", False)
    item = TrackedItem(name="x", keywords="kw")
    db.add(item)
    await db.commit()
    matcher = SemanticMatcher(db, ai=_FakeAI([1.0, 0.0]))
    count = await matcher.embed_and_store_items()
    assert count == 0
    await db.refresh(item)
    assert item.embedding is None


async def test_embed_and_store_populates_when_enabled(monkeypatch, db):
    monkeypatch.setattr(settings, "ENABLE_SEMANTIC_MATCHING", True)
    monkeypatch.setattr(settings, "AI_ENABLED", True)
    item = TrackedItem(name="EPYC 7763", keywords="epyc 7763")
    db.add(item)
    await db.commit()
    matcher = SemanticMatcher(db, ai=_FakeAI([0.5, 0.5]))
    count = await matcher.embed_and_store_items()
    assert count == 1
    await db.refresh(item)
    assert list(item.embedding) == [0.5, 0.5]
