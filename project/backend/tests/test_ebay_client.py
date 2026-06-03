"""story-005: eBay client filter-fixture unit test + creds-gated real_ebay smoke test.

The filter unit test is a regression guard for the already-fixed client.py (the old
code emitted a literal "{'|'.join(...)}" brace bug). It does NOT modify client.py and
makes no network call (OAuth + HTTP layers are patched).
"""
import os

import httpx
import pytest
from sqlalchemy import select

from app.models.listing import Listing
from app.models.tracked_item import TrackedItem
from app.services.ebay.client import EbayBrowseClient, EbayOAuthClient
from app.services.ebay.poller import EbayPoller


class _FakeResponse:
    def raise_for_status(self):
        pass

    def json(self):
        return {"itemSummaries": [], "total": 0}


async def test_browse_filter_string_is_canonical(monkeypatch):
    captured = {}

    async def fake_get(self, url, headers=None, params=None):
        captured["params"] = params
        return _FakeResponse()

    async def fake_token(self):
        return "fake-token"

    monkeypatch.setattr(EbayOAuthClient, "get_token", fake_token)
    monkeypatch.setattr(httpx.AsyncClient, "get", fake_get)

    client = EbayBrowseClient()
    await client.search(
        keywords="EPYC 7F72",
        buying_options=["FIXED_PRICE", "AUCTION"],
        condition_ids=["1000", "3000"],
        min_price=50,
        max_price=200,
    )

    flt = captured["params"]["filter"]
    # Canonical fragments present and correctly brace-wrapped (catches the old f-string bug).
    assert "buyingOptions:{FIXED_PRICE|AUCTION}" in flt
    assert "conditionIds:{1000|3000}" in flt
    assert "price:[50..200],priceCurrency:USD" in flt
    # Fragments are comma-joined (not concatenated): proves ordering + separator.
    assert "buyingOptions:{FIXED_PRICE|AUCTION},conditionIds:{1000|3000}" in flt


_REAL_EBAY_READY = (
    bool(os.getenv("EBAY_APP_ID"))
    and bool(os.getenv("EBAY_CERT_ID"))
    and os.getenv("USE_MOCK_EBAY", "true").lower() == "false"
)


@pytest.mark.real_ebay
@pytest.mark.skipif(
    not _REAL_EBAY_READY,
    reason="real eBay creds not set or USE_MOCK_EBAY != false",
)
async def test_real_ebay_smoke_persists_listing(db):
    item = TrackedItem(
        name="EPYC 7F72",
        keywords="EPYC 7F72",
        benchmark_median=350,
        scam_floor=10,
        search_interval=600,
        is_enabled=True,
    )
    db.add(item)
    await db.flush()

    poller = EbayPoller()
    await poller.search_item(db, item)
    await db.flush()

    listings = (await db.execute(select(Listing).where(Listing.tracked_item_id == item.id))).scalars().all()
    assert len(listings) >= 1
