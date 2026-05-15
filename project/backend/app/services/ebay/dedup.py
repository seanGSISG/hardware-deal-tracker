from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.listing import Listing


class DeduplicationEngine:
    """Prevent duplicate listings from being stored."""

    async def is_duplicate(self, db: AsyncSession, marketplace_id: str) -> bool:
        result = await db.execute(select(Listing).where(Listing.marketplace_id == marketplace_id))
        return result.scalar_one_or_none() is not None

    async def dedup_batch(self, db: AsyncSession, listings: list) -> tuple[list, int]:
        new_listings = []
        duplicates = 0
        for listing in listings:
            exists = await self.is_duplicate(db, listing["marketplace_id"])
            if not exists:
                new_listings.append(listing)
            else:
                duplicates += 1
        return new_listings, duplicates
