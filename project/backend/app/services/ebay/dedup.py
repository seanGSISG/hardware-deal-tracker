from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.listing import Listing

DEFAULT_SOURCE = "ebay"


class DeduplicationEngine:
    """Prevent duplicate listings from being stored.

    Dedup key is the (source, marketplace_id) pair (feature-005): the same raw
    listing id can legitimately appear under two different sources, so the source
    must be part of the identity. Listings without an explicit ``source`` default
    to ``ebay`` for backward compatibility with the original eBay-only path.
    """

    async def is_duplicate(self, db: AsyncSession, marketplace_id: str, source: str = DEFAULT_SOURCE) -> bool:
        result = await db.execute(
            select(Listing).where(
                Listing.source == source,
                Listing.marketplace_id == marketplace_id,
            )
        )
        return result.scalar_one_or_none() is not None

    async def dedup_batch(self, db: AsyncSession, listings: list) -> tuple[list, int]:
        new_listings = []
        duplicates = 0
        seen: set[tuple[str, str]] = set()
        for listing in listings:
            source = listing.get("source", DEFAULT_SOURCE)
            key = (source, listing["marketplace_id"])
            if key in seen:
                duplicates += 1
                continue
            exists = await self.is_duplicate(db, listing["marketplace_id"], source)
            if not exists:
                seen.add(key)
                new_listings.append(listing)
            else:
                duplicates += 1
        return new_listings, duplicates
