"""Generic ShopifyJsonLdAdapter (feature-005, story-E).

Most independent US used-server retailers run Shopify, exposing a public, stable
`/products.json` endpoint plus schema.org `Product`/`Offer` JSON-LD. This ONE
adapter serves all of them, driven purely by a per-source `ShopifySourceConfig`
(TechMikeNY -> UnixSurplus -> ServerMonkey). Listings normalize to the shared
shape and dedup by `(source, variant id)`, so a TechMikeNY item appearing in both
its own site and the eBay feed is de-duplicated.

Transport is injected and mockable; tests NEVER hit a live store. A best-effort
httpx transport lives in `shopify_transport.py`.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from app.core.config import settings
from app.services.sources.base import NormalizedListing, SourceAdapter
from app.services.sources.rate_budget import SourceRateBudget


@dataclass
class ShopifySourceConfig:
    """Per-retailer configuration — the only thing that differs between sources."""

    source: str
    base_url: str
    merchant: str
    currency: str = "USD"
    # Default condition for the store (most used-server retailers list refurb/used).
    default_condition: str = "Used"


class ShopifyTransport(Protocol):
    """Injected transport contract for fetching a store's /products.json."""

    async def fetch_products_json(self, base_url: str, query: str, page: int = 1) -> dict: ...


def _matches(title: str, keywords: str) -> bool:
    """Lightweight keyword match: every whitespace token must appear in title."""
    title_l = title.lower()
    return all(tok in title_l for tok in keywords.lower().split())


class ShopifyJsonLdAdapter(SourceAdapter):
    """Generic Shopify `/products.json` + JSON-LD adapter, configured per source."""

    def __init__(
        self,
        config: ShopifySourceConfig,
        transport: ShopifyTransport,
        enabled: bool | None = None,
        daily_limit: int | None = None,
        budget: SourceRateBudget | None = None,
    ):
        self.config = config
        self.source = config.source
        self.transport = transport
        self.enabled = settings.ENABLE_SHOPIFY_SOURCES if enabled is None else enabled
        limit = settings.SHOPIFY_SOURCE_DAILY_LIMIT if daily_limit is None else daily_limit
        self.budget = budget or SourceRateBudget()
        self.budget.configure(self.source, daily_limit=limit)

    async def search(self, catalog_item) -> list[NormalizedListing]:
        if not self.enabled:
            return []
        if not self.budget.can_call(self.source):
            return []

        self.budget.record_call(self.source)
        payload = await self.transport.fetch_products_json(
            self.config.base_url, catalog_item.keywords
        )
        return self._normalize(payload, catalog_item)

    def _normalize(self, payload: dict, catalog_item) -> list[NormalizedListing]:
        out: list[NormalizedListing] = []
        for product in payload.get("products", []):
            title = product.get("title", "")
            if not _matches(title, catalog_item.keywords):
                continue
            handle = product.get("handle", "")
            for variant in product.get("variants", []):
                if not variant.get("available", True):
                    continue
                try:
                    price = float(variant.get("price"))
                except (TypeError, ValueError):
                    continue
                variant_id = str(variant.get("id"))
                out.append(
                    NormalizedListing(
                        source=self.source,
                        source_listing_id=variant_id,
                        title=title,
                        url=f"{self.config.base_url}/products/{handle}?variant={variant_id}",
                        price=price,
                        currency=self.config.currency,
                        shipping=0.0,
                        condition=self.config.default_condition,
                        availability="in_stock",
                        seller=self.config.merchant,
                        catalog_item_id=catalog_item.id,
                        raw_payload={"product": product, "variant": variant},
                    )
                )
        return out
