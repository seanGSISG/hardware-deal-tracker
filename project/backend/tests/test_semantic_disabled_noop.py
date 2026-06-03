"""story-5 (feature-006): the OPTIONAL semantic feature is inert when off.

Proves the core app is unaffected with ENABLE_SEMANTIC_MATCHING false (the
default) and/or AI_ENABLED false: the matcher and embed paths are no-ops, the
endpoint returns a clean disabled shape, and no semantic/pgvector code path is
reached. Runs entirely on the in-memory sqlite suite with embeddings mocked.
"""
from app.core.config import settings
from app.models.listing import Listing
from app.models.tracked_item import TrackedItem
from app.services.ai.client import AIClient
from app.services.semantic.matcher import SemanticMatcher


def test_config_default_is_off():
    """The feature ships off; a fresh Settings has it disabled."""
    from app.core.config import Settings

    assert Settings().ENABLE_SEMANTIC_MATCHING is False
    assert settings.ENABLE_SEMANTIC_MATCHING is False


async def test_matcher_inert_when_feature_disabled(monkeypatch, db):
    """ENABLE_SEMANTIC_MATCHING false -> every entry point is a no-op."""
    monkeypatch.setattr(settings, "ENABLE_SEMANTIC_MATCHING", False)
    monkeypatch.setattr(settings, "AI_ENABLED", True)
    monkeypatch.setattr(settings, "OPENROUTER_API_KEY", "sk-test")

    item = TrackedItem(name="EPYC 7763", keywords="epyc 7763", embedding=[1.0, 0.0])
    db.add(item)
    await db.commit()

    matcher = SemanticMatcher(db)
    assert matcher.is_enabled is False
    listing = Listing(marketplace_id="x", title="EPYC 7763", price=1, seller="s", url="http://x")
    assert await matcher.suggest_catalog_item(listing) is None
    assert await matcher.similar_items(item) == []
    assert await matcher.embed_and_store_items() == 0


async def test_matcher_inert_when_ai_disabled(monkeypatch, db):
    """AI_ENABLED false -> embed() None and suggest/similar empty, no errors."""
    monkeypatch.setattr(settings, "ENABLE_SEMANTIC_MATCHING", True)
    monkeypatch.setattr(settings, "AI_ENABLED", False)

    item = TrackedItem(name="EPYC 7763", keywords="epyc 7763", embedding=[1.0, 0.0])
    db.add(item)
    await db.commit()

    assert await AIClient().embed("EPYC 7763") is None
    matcher = SemanticMatcher(db)
    assert matcher.is_enabled is False
    listing = Listing(marketplace_id="x", title="EPYC 7763", price=1, seller="s", url="http://x")
    assert await matcher.suggest_catalog_item(listing) is None
    assert await matcher.similar_items(item) == []


async def test_endpoint_disabled_shape(client):
    """With the default config the endpoint is a clean disabled no-op (no 500)."""
    # Default settings -> ENABLE_SEMANTIC_MATCHING false.
    resp = await client.get("/api/v1/semantic/similar/1")
    assert resp.status_code == 200
    body = resp.json()
    assert body == {"enabled": False, "item_id": 1, "similar": []}


async def test_poll_path_unaffected_by_feature(monkeypatch):
    """The poll/score path yields identical results regardless of the feature flag.

    Semantic matching is intentionally NOT wired into EbayPoller, so toggling the
    flag must not change scoring output. Each flag value runs against its own
    fresh in-memory DB (so there is no cross-run dedup) with the RNG seeded
    identically, so any score difference would be attributable to the flag alone.
    """
    import random

    from sqlalchemy import select
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
    from sqlalchemy.pool import StaticPool

    from app.models import Base
    from app.models.listing_score import ListingScore
    from app.services.ebay.poller import EbayPoller

    async def _run_once(flag: bool) -> list[int]:
        random.seed(1234)
        monkeypatch.setattr(settings, "ENABLE_SEMANTIC_MATCHING", flag)
        eng = create_async_engine(
            "sqlite+aiosqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        async with eng.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        factory = async_sessionmaker(eng, class_=AsyncSession, expire_on_commit=False)
        async with factory() as session:
            item = TrackedItem(
                name="EPYC 7F72", keywords="EPYC 7F72",
                benchmark_median=350, scam_floor=10, search_interval=600,
            )
            session.add(item)
            await session.flush()
            await EbayPoller().search_item(session, item)
            await session.flush()
            scores = (
                await session.execute(
                    select(ListingScore)
                    .where(ListingScore.tracked_item_id == item.id)
                    .order_by(ListingScore.listing_id)
                )
            ).scalars().all()
            result = [s.overall_score for s in scores]
        await eng.dispose()
        return result

    off = await _run_once(False)
    on = await _run_once(True)
    assert off, "expected scored listings from the mock poll"
    assert off == on  # the flag does not perturb scoring
