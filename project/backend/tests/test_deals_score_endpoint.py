"""Regression test for the deals score endpoint F821 bug.

`POST /api/v1/deals/score/{listing_id}` referenced `TrackedItem` without importing
it (ruff F821 undefined-name). Any listing carrying a `tracked_item_id` triggered a
`NameError` at runtime. This test scores such a listing end-to-end to prove the name
resolves.
"""
from datetime import datetime

import pytest

from app.models.listing import Listing
from app.models.tracked_item import TrackedItem


@pytest.mark.asyncio
async def test_score_listing_with_tracked_item(client, db):
    item = TrackedItem(
        name="AMD EPYC 7302",
        keywords="EPYC 7302",
        benchmark_median=300.0,
    )
    db.add(item)
    await db.flush()

    listing = Listing(
        source="ebay",
        marketplace_id="v1|test-score-1|0",
        tracked_item_id=item.id,
        title="AMD EPYC 7302 16-core",
        price=250.0,
        shipping=0,
        seller="seller1",
        url="https://example.com/1",
        listing_date=datetime.utcnow(),
    )
    db.add(listing)
    await db.flush()

    resp = await client.post(f"/api/v1/deals/score/{listing.id}")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert "overall_score" in body or "score" in body
