"""Real (best-effort) PCPartPicker transport (feature-005, story-D).

This is the production transport injected into `PcPartPickerAdapter`. It is a
thin, polite HTML fetcher + parser for a single product page. It is intentionally
minimal and NOT exercised in tests (tests always inject a fake transport).

Reality check (see plan/MVP2_PCPARTPICKER_RESEARCH.md): PCPartPicker is behind
Cloudflare and its ToS forbids scraping, so this default `httpx` transport WILL
often get a 403 from datacenter IPs. The adapter's circuit breaker handles that
gracefully. For real use, swap in a TLS-impersonating fetcher (`curl_cffi`) routed
through a residential egress; that escalation is deliberately left as a pluggable
transport rather than a hard dependency here.
"""
from __future__ import annotations

import json
import re

import httpx

from app.services.sources.pcpartpicker import PcppPart, PcppPrice, PcppVendor

_BASE = "https://pcpartpicker.com"
# Schema.org Offer blocks embedded as JSON-LD on product pages.
_JSONLD_RE = re.compile(r'<script[^>]+type="application/ld\+json"[^>]*>(.*?)</script>', re.DOTALL)


class HttpxPcppTransport:
    """Best-effort product-page fetcher. Override for residential/curl_cffi egress."""

    def __init__(self, base_url: str = _BASE, timeout: float = 20.0, headers: dict | None = None):
        self.base_url = base_url
        self.timeout = timeout
        self.headers = headers or {
            "User-Agent": "Mozilla/5.0 (compatible; HardwareDealTracker/1.0)",
            "Accept": "text/html,application/xhtml+xml",
        }

    async def fetch_part(self, product_id: str, region: str = "us") -> PcppPart:
        url = f"{self.base_url}/product/{product_id}/"
        async with httpx.AsyncClient(timeout=self.timeout, headers=self.headers) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            html = resp.text
        return self._parse(product_id, url, html)

    @staticmethod
    def _parse(product_id: str, url: str, html: str) -> PcppPart:
        name = product_id
        vendors: list[PcppVendor] = []
        for raw in _JSONLD_RE.findall(html):
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                continue
            blocks = data if isinstance(data, list) else [data]
            for block in blocks:
                if not isinstance(block, dict):
                    continue
                if block.get("name"):
                    name = block["name"]
                offers = block.get("offers")
                if not offers:
                    continue
                if isinstance(offers, dict):
                    offers = [offers]
                for offer in offers:
                    try:
                        total = float(offer.get("price"))
                    except (TypeError, ValueError):
                        continue
                    in_stock = "instock" in str(offer.get("availability", "")).lower()
                    vendors.append(
                        PcppVendor(
                            name=str(offer.get("seller", {}).get("name", "unknown"))
                            if isinstance(offer.get("seller"), dict)
                            else "unknown",
                            in_stock=in_stock or offer.get("availability") is None,
                            price=PcppPrice(
                                base=total,
                                shipping=0.0,
                                total=total,
                                currency=offer.get("priceCurrency", "USD"),
                            ),
                        )
                    )
        return PcppPart(product_id=product_id, name=name, type="unknown", url=url, vendors=vendors)
