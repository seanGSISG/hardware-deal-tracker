"""eBay Browse API as the first SourceAdapter (feature-005, story-B).

Wraps the existing `EbayBrowseClient`/`MockEbayClient` + `ListingParser` behind
the `SourceAdapter` contract. The poller delegates its eBay fetch+parse to this
adapter; the adapter exposes both:

- `search(catalog_item)` -> normalized listings (the SourceAdapter contract), and
- a rich eBay listing-row dict stashed in each listing's
  ``raw_payload["_listing_row"]`` so the poller can persist the full eBay-shaped
  `Listing` (seller feedback, condition ids, etc.) without regressing scoring.
"""
from __future__ import annotations

from app.core.config import settings
from app.services.ebay.client import EbayBrowseClient
from app.services.ebay.mock import MockEbayClient
from app.services.ebay.parser import ListingParser
from app.services.sources.base import NormalizedListing, SourceAdapter


class EbayBrowseAdapter(SourceAdapter):
    """Normalize eBay Browse search results into the shared listing shape."""

    source = "ebay"

    def __init__(self, client=None, parser: ListingParser | None = None):
        if client is not None:
            self.client = client
        elif settings.USE_MOCK_EBAY:
            self.client = MockEbayClient()
        else:
            self.client = EbayBrowseClient()
        self.parser = parser or ListingParser()

    async def fetch_raw(self, catalog_item) -> dict:
        """Raw eBay Browse response for a catalog item (kept for the poller)."""
        return await self.client.search(
            keywords=catalog_item.keywords,
            category_id=catalog_item.category_id,
            buying_options=["FIXED_PRICE", "AUCTION"],
        )

    def to_listing_rows(self, response: dict, catalog_item) -> list[dict]:
        """Rich eBay-shaped listing dicts (the existing parser output)."""
        return self.parser.parse_search_response(response, catalog_item.id)

    async def search(self, catalog_item) -> list[NormalizedListing]:
        response = await self.fetch_raw(catalog_item)
        rows = self.to_listing_rows(response, catalog_item)
        out: list[NormalizedListing] = []
        for row in rows:
            out.append(
                NormalizedListing(
                    source=self.source,
                    source_listing_id=row["marketplace_id"],
                    title=row["title"],
                    url=row["url"],
                    price=float(row["price"]),
                    currency="USD",
                    shipping=float(row.get("shipping") or 0.0),
                    condition=row.get("condition"),
                    availability=None,
                    seller=row.get("seller"),
                    catalog_item_id=catalog_item.id,
                    # Stash the full eBay-shaped row so the poller can persist a
                    # rich Listing (and so scoring keeps all eBay signals).
                    raw_payload={**row.get("raw_data", {}), "_listing_row": row},
                )
            )
        return out
