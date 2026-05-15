import time
from datetime import datetime
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, text
from app.core.config import settings
from app.services.ebay.client import EbayBrowseClient
from app.services.ebay.mock import MockEbayClient
from app.services.ebay.parser import ListingParser
from app.services.ebay.dedup import DeduplicationEngine
from app.services.ebay.rate_budget import RateBudgetManager
from app.models.tracked_item import TrackedItem
from app.models.listing import Listing


class EbayPoller:
    """Orchestrates tiered eBay searches with rate budget protection."""

    PRESETS = {
        "hot": 300,
        "standard": 600,
        "monitor": 1200,
        "passive": 1800,
    }

    def __init__(self, redis_client=None):
        if settings.USE_MOCK_EBAY:
            self.client = MockEbayClient()
        else:
            self.client = EbayBrowseClient()
        self.parser = ListingParser()
        self.dedup = DeduplicationEngine()
        self.budget = RateBudgetManager(redis_client)

    async def get_items_due(self, db: AsyncSession) -> List[TrackedItem]:
        now = datetime.utcnow()
        result = await db.execute(
            select(TrackedItem)
            .where(
                and_(
                    TrackedItem.is_enabled == True,
                    TrackedItem.last_searched == None
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
                    TrackedItem.is_enabled == True,
                    TrackedItem.last_searched != None,
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
            response = await self.client.search(
                keywords=item.keywords,
                category_id=item.category_id,
                buying_options=["FIXED_PRICE", "AUCTION"]
            )
            await self.budget.record_call()

            raw_listings = self.parser.parse_search_response(response, item.id)
            new_listings, duplicates = await self.dedup.dedup_batch(db, raw_listings)

            for listing_data in new_listings:
                listing = Listing(**listing_data)
                db.add(listing)

            item.last_searched = datetime.utcnow()
            await db.flush()

            duration = int((time.time() - start_time) * 1000)
            budget_status = await self.budget.get_budget_status()

            return {
                "listings_found": len(raw_listings),
                "new_listings": len(new_listings),
                "duplicates_skipped": duplicates,
                "duration_ms": duration,
                "priority": priority,
                "budget": budget_status
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
