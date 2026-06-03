"""story-004: /search/trigger* endpoints actually poll, with 429 + Retry-After.

Replaces the hardcoded stub responses with real EbayPoller calls, and returns
HTTP 429 (with Retry-After) when the eBay rate budget is exhausted.
"""
from sqlalchemy import select

from app.models.listing_score import ListingScore
from app.models.tracked_item import TrackedItem
from app.services.ebay.rate_budget import RateBudgetManager


async def _seed_item(db) -> TrackedItem:
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
    return item


async def test_trigger_missing_item_returns_404(client):
    resp = await client.post("/api/v1/search/trigger/9999")
    assert resp.status_code == 404


async def test_trigger_item_returns_real_poller_result(client, db):
    item = await _seed_item(db)

    resp = await client.post(f"/api/v1/search/trigger/{item.id}")
    assert resp.status_code == 200
    body = resp.json()
    # Real mock-poller output, not the old hardcoded zeros.
    assert body["listings_found"] >= 1
    assert body["new_listings"] >= 1

    # Listings were actually persisted AND scored (story-002 wiring) through the endpoint.
    scores = (await db.execute(select(ListingScore).where(ListingScore.tracked_item_id == item.id))).scalars().all()
    assert len(scores) == body["new_listings"]


async def test_trigger_all_returns_real_aggregate(client, db):
    await _seed_item(db)

    resp = await client.post("/api/v1/search/trigger-all")
    assert resp.status_code == 200
    body = resp.json()
    # Real aggregate keys from EbayPoller.search_all, not the hardcoded stub.
    assert "items_processed" in body
    assert "total_listings" in body
    assert "total_new" in body


async def test_trigger_item_429_when_budget_exhausted(client, db, monkeypatch):
    item = await _seed_item(db)

    async def _exhausted(self, priority="P1"):
        return False

    monkeypatch.setattr(RateBudgetManager, "can_search", _exhausted)

    resp = await client.post(f"/api/v1/search/trigger/{item.id}")
    assert resp.status_code == 429
    assert "Retry-After" in resp.headers
    assert int(resp.headers["Retry-After"]) > 0


async def test_trigger_all_429_when_budget_exhausted(client, db, monkeypatch):
    await _seed_item(db)

    async def _exhausted(self, priority="P1"):
        return False

    monkeypatch.setattr(RateBudgetManager, "can_search", _exhausted)

    resp = await client.post("/api/v1/search/trigger-all")
    assert resp.status_code == 429
    assert "Retry-After" in resp.headers
    assert int(resp.headers["Retry-After"]) > 0
