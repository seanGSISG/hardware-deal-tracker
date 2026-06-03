"""Real (best-effort) Shopify transport (feature-005, story-E).

Fetches a store's public `/products.json` (paginated) and returns the parsed
dict that `ShopifyJsonLdAdapter` normalizes. Injected in production; tests always
inject a fake transport, so this is never exercised in the test suite.

`/products.json` returns ALL products (250/page); we fetch a bounded number of
pages and let the adapter keyword-filter. Always check each store's robots.txt /
ToS before enabling it (per source research).
"""
from __future__ import annotations

import httpx


class HttpxShopifyTransport:
    """Best-effort `/products.json` fetcher for a Shopify-class store."""

    def __init__(self, timeout: float = 20.0, max_pages: int = 3, headers: dict | None = None):
        self.timeout = timeout
        self.max_pages = max_pages
        self.headers = headers or {
            "User-Agent": "Mozilla/5.0 (compatible; HardwareDealTracker/1.0)",
            "Accept": "application/json",
        }

    async def fetch_products_json(self, base_url: str, query: str, page: int = 1) -> dict:
        products: list[dict] = []
        async with httpx.AsyncClient(timeout=self.timeout, headers=self.headers) as client:
            for p in range(page, page + self.max_pages):
                resp = await client.get(
                    f"{base_url.rstrip('/')}/products.json",
                    params={"limit": 250, "page": p},
                )
                resp.raise_for_status()
                batch = resp.json().get("products", [])
                if not batch:
                    break
                products.extend(batch)
        return {"products": products}
