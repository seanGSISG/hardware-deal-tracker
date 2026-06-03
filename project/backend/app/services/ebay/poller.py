import logging
import time
from datetime import datetime

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.listing import Listing
from app.models.listing_score import ListingScore
from app.models.price_history import PriceHistory
from app.models.tracked_item import TrackedItem
from app.services.ai.analysis import AIAnalyzer
from app.services.ebay.dedup import DeduplicationEngine
from app.services.ebay.rate_budget import RateBudgetManager
from app.services.notifications.dispatcher import NotificationDispatcher
from app.services.scoring.engine import DealScoringEngine
from app.services.sources.ebay import EbayBrowseAdapter

logger = logging.getLogger(__name__)


class EbayPoller:
    """Orchestrates tiered eBay searches with rate budget protection.

    eBay ingestion is delegated to an `EbayBrowseAdapter` (feature-005, the first
    `SourceAdapter`). `self.client` / `self.parser` proxy to the adapter so older
    call sites and tests that override `poller.client` keep working.
    """

    PRESETS = {
        "hot": 300,
        "standard": 600,
        "monitor": 1200,
        "passive": 1800,
    }

    def __init__(self, redis_client=None):
        self.adapter = EbayBrowseAdapter()
        self.dedup = DeduplicationEngine()
        self.budget = RateBudgetManager(redis_client)
        self.scorer = DealScoringEngine()
        self.dispatcher = NotificationDispatcher()
        self.analyzer = AIAnalyzer()
        # Multi-source fan-out (feature-003, ADR-003): the enabled + robots/ToS
        # verified Shopify adapters, each with its own SourceRateBudget bucket
        # (isolated from eBay's 5000/day RateBudgetManager). Built lazily so the
        # default (no real network) test poller stays eBay-only unless a test or
        # config opts in. Tests may override `poller.shopify_adapters` directly.
        self.shopify_adapters = self._build_shopify_adapters()

    def _build_shopify_adapters(self):
        """Construct enabled+verified Shopify SourceAdapters from the registry."""
        from app.services.sources.shopify_sources import build_shopify_adapters
        from app.services.sources.shopify_transport import HttpxShopifyTransport

        try:
            return build_shopify_adapters(transport=HttpxShopifyTransport())
        except Exception:  # noqa: BLE001 — never let source wiring break the poller
            logger.exception("failed to build Shopify adapters; continuing eBay-only")
            return []

    async def _fetch_shopify_rows(self, item: TrackedItem) -> tuple[list[dict], list[dict]]:
        """Fan out across Shopify adapters (graceful degradation).

        Returns (listing_rows, source_errors). A single source's failure is
        captured per-source and never aborts the others or the eBay path. Each
        adapter enforces its OWN rate bucket internally, so an exhausted source
        simply returns [] without touching any other source or eBay's budget.
        """
        rows: list[dict] = []
        errors: list[dict] = []
        for adapter in self.shopify_adapters:
            source = getattr(adapter, "source", "shopify")
            try:
                normalized = await adapter.search(item)
            except Exception as exc:  # noqa: BLE001 — degrade, don't abort
                logger.exception("Shopify source %s failed", source)
                errors.append({"source": source, "error": str(exc)})
                continue
            for nl in normalized:
                rows.append(nl.to_listing_row())
        return rows, errors

    @property
    def client(self):
        return self.adapter.client

    @client.setter
    def client(self, value):
        self.adapter.client = value

    @property
    def parser(self):
        return self.adapter.parser

    @parser.setter
    def parser(self, value):
        self.adapter.parser = value

    def _historical_stats_for(self, item: TrackedItem) -> dict:
        """Historical price stats for an item, used by the scoring engine.

        Seam (ADR-006): returns an empty dict today, so the scorer takes the
        catalog-benchmark fallback path (catalog_item.benchmark_median).
        feature-006 (price history) will replace this with real per-item stats.
        """
        return {}

    async def get_items_due(self, db: AsyncSession) -> list[TrackedItem]:
        now = datetime.utcnow()
        result = await db.execute(
            select(TrackedItem)
            .where(
                and_(
                    TrackedItem.is_enabled.is_(True),
                    TrackedItem.last_searched.is_(None)
                )
            )
            .order_by(TrackedItem.created_at.desc())
            .limit(10)
        )
        never_searched = list(result.scalars().all())

        result = await db.execute(
            select(TrackedItem)
            .where(
                and_(
                    TrackedItem.is_enabled.is_(True),
                    TrackedItem.last_searched.is_not(None),
                )
            )
            .order_by(
                TrackedItem.search_interval.asc(),
                TrackedItem.last_searched.asc()
            )
            .limit(20)
        )
        due_items = list(result.scalars().all())

        filtered = []
        for item in due_items:
            if item.last_searched and (now - item.last_searched).total_seconds() >= item.search_interval:
                filtered.append(item)

        return never_searched + filtered

    async def search_item(self, db: AsyncSession, item: TrackedItem) -> dict:
        start_time = time.time()
        priority = self.budget.get_priority_for_interval(item.search_interval)
        can_search = await self.budget.can_search(priority)
        if not can_search:
            return {
                "listings_found": 0, "new_listings": 0, "duplicates_skipped": 0,
                "duration_ms": 0, "skipped": True, "reason": "Rate budget exhausted",
                "priority": priority
            }

        try:
            # Delegate eBay fetch+normalize to the SourceAdapter (feature-005).
            # The adapter stashes the rich eBay-shaped Listing row in each
            # listing's raw_payload["_listing_row"], so dedup/persist/scoring keep
            # all eBay signals (seller feedback, condition ids, etc.).
            normalized = await self.adapter.search(item)
            await self.budget.record_call()

            raw_listings = [nl.raw_payload["_listing_row"] for nl in normalized]

            # Multi-source fan-out (feature-003): append Shopify rows so they flow
            # through the SAME dedup -> persist -> score -> price-history path.
            # Each Shopify source draws from its own bucket (isolated from eBay's
            # 5000/day budget); a failing source degrades gracefully.
            shopify_rows, source_errors = await self._fetch_shopify_rows(item)
            raw_listings.extend(shopify_rows)

            new_listings, duplicates = await self.dedup.dedup_batch(db, raw_listings)

            listings = []
            for listing_data in new_listings:
                listing = Listing(**listing_data)
                db.add(listing)
                listings.append(listing)

            item.last_searched = datetime.utcnow()
            # Flush so each new Listing gets its primary key before scoring (ADR-006).
            await db.flush()

            # Score each new listing and persist a ListingScore (keystone gap fix).
            historical_stats = self._historical_stats_for(item)
            scored = 0
            scored_pairs = []
            for listing in listings:
                score = self.scorer.calculate_overall_score(listing, historical_stats, catalog_item=item)
                db.add(
                    ListingScore(
                        listing_id=listing.id,
                        tracked_item_id=item.id,
                        overall_score=score["overall_score"],
                        deal_score=score["deal_score"],
                        confidence=score["confidence"],
                        classification=score["classification"],
                        price_zscore=score["price_zscore"],
                        vs_median_pct=score["vs_median_pct"],
                        vs_lowest_pct=score["vs_lowest_pct"],
                        est_fair_value=score["est_fair_value"],
                        scam_flag=score["scam_warning"],
                    )
                )
                # Record a price-history point for this poll snapshot (feature-006).
                db.add(
                    PriceHistory(
                        listing_id=listing.id,
                        tracked_item_id=item.id,
                        observed_price=listing.price,
                        shipping=listing.shipping,
                        total_price=float(listing.price) + float(listing.shipping),
                    )
                )
                scored_pairs.append((listing, score))
                scored += 1
            await db.flush()

            # Best-effort notification fan-out (T2.3). Never let a dispatch
            # failure tear down the poll/score path.
            for listing, score in scored_pairs:
                try:
                    await self.dispatcher.dispatch_for_deal(db, listing, score)
                except Exception:
                    logger.exception("dispatch failed for listing %s", listing.id)

            # Best-effort AI deal analysis (feature-006). Opt-in + non-fatal.
            if self.analyzer.is_enabled:
                for listing, _ in scored_pairs:
                    try:
                        await self.analyzer.analyze_listing(db, listing, catalog_item=item)
                    except Exception:
                        logger.exception("AI analysis failed for listing %s", listing.id)

            duration = int((time.time() - start_time) * 1000)
            budget_status = await self.budget.get_budget_status()

            return {
                "listings_found": len(raw_listings),
                "new_listings": len(new_listings),
                "listings_scored": scored,
                "duplicates_skipped": duplicates,
                "duration_ms": duration,
                "priority": priority,
                "budget": budget_status,
                "source_errors": source_errors,
            }
        except Exception as e:
            return {
                "listings_found": 0, "new_listings": 0, "duplicates_skipped": 0,
                "duration_ms": 0, "error": str(e), "priority": priority
            }

    async def search_all(self, db: AsyncSession) -> dict:
        items = await self.get_items_due(db)
        total_results = {
            "items_due": len(items),
            "items_processed": 0, "items_skipped": 0,
            "total_listings": 0, "total_new": 0,
            "total_duplicates": 0, "errors": [],
            "budget": await self.budget.get_budget_status()
        }

        for item in items:
            priority = self.budget.get_priority_for_interval(item.search_interval)
            if not await self.budget.can_search(priority):
                total_results["items_skipped"] += 1
                continue

            result = await self.search_item(db, item)
            if result.get("skipped"):
                total_results["items_skipped"] += 1
            else:
                total_results["items_processed"] += 1
                total_results["total_listings"] += result["listings_found"]
                total_results["total_new"] += result["new_listings"]
                total_results["total_duplicates"] += result["duplicates_skipped"]
            if "error" in result:
                total_results["errors"].append({"item": item.name, "error": result["error"]})

        total_results["budget"] = await self.budget.get_budget_status()
        return total_results

    async def get_budget_status(self) -> dict:
        return await self.budget.get_budget_status()

    @classmethod
    def get_preset_interval(cls, preset: str) -> int:
        return cls.PRESETS.get(preset, 600)
