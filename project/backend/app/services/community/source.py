"""CommunitySignalSource — the gated leads-pipeline orchestrator (feature-007).

This class is ADJACENT to the structured SourceAdapter price-poll path. It pulls
community posts, AI-extracts structured leads, drops sold/traded + duplicate
posts, and (when given a session) persists the survivors into the
``community_signal_leads`` table. It NEVER emits a NormalizedListing and never
touches scoring/notifications.

The single ``ingest`` entrypoint is a pure no-op returning ``[]`` (zero network,
zero AI) when ENABLE_COMMUNITY_SIGNAL is False.
"""
from __future__ import annotations

import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.services.community.dedup import dedup_leads, filter_stale
from app.services.community.extractor import CommunityLeadExtractor
from app.services.community.reddit import RedditClient
from app.services.community.types import CommunityLead, CommunityPost
from app.services.sources.rate_budget import SourceRateBudget

logger = logging.getLogger(__name__)

# The community bucket key — distinct from eBay's RateBudgetManager budget.
COMMUNITY_SOURCE_KEY = "reddit_homelabsales"


class CommunitySignalSource:
    def __init__(
        self,
        *,
        budget: SourceRateBudget | None = None,
        extractor: CommunityLeadExtractor | None = None,
    ):
        # Own polite per-source bucket; NEVER eBay's 5000/day RateBudgetManager.
        self.budget = budget or SourceRateBudget(
            default_daily_limit=settings.COMMUNITY_SIGNAL_DAILY_LIMIT
        )
        self.budget.configure(COMMUNITY_SOURCE_KEY, settings.COMMUNITY_SIGNAL_DAILY_LIMIT)
        self.extractor = extractor or CommunityLeadExtractor()

    @property
    def is_enabled(self) -> bool:
        return settings.ENABLE_COMMUNITY_SIGNAL

    async def _fetch_posts(self) -> list[CommunityPost]:
        """Fetch raw posts from the configured community source(s).

        Degrades to [] on any error / missing creds (RedditClient is itself
        defensive). Calls are recorded against the polite community bucket.
        """
        client = RedditClient(self.budget, source_key=COMMUNITY_SOURCE_KEY)
        return await client.fetch_new(limit=settings.COMMUNITY_SIGNAL_FETCH_LIMIT)

    async def _extract(self, db: AsyncSession | None, post: CommunityPost) -> CommunityLead | None:
        return await self.extractor.extract(db, post)

    async def ingest(self, db: AsyncSession | None = None) -> list[CommunityLead]:
        """Run one ingest cycle and return surviving (live, deduped) leads.

        No-op returning [] when the gate is off — zero network, zero AI work.
        When ``db`` is provided, surviving leads are persisted to the leads
        table (story-5); persistence never touches scoring/notifications.
        """
        if not self.is_enabled:
            return []

        posts = await self._fetch_posts()
        leads: list[CommunityLead] = []
        for post in posts:
            lead = await self._extract(db, post)
            if lead is not None:
                leads.append(lead)

        # Drop sold/traded/pending leads, then dedup on (source, source_post_id).
        leads = dedup_leads(filter_stale(leads))

        if db is not None and leads:
            from app.services.community.persistence import persist_leads

            await persist_leads(db, leads)

        logger.info("community ingest: fetched=%s persisted=%s", len(posts), len(leads))
        return leads
