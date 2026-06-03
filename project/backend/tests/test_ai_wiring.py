"""story-5 (feature-006): AI wired into the poll path (best-effort) + AI endpoint."""
import json
from datetime import datetime

from sqlalchemy import select

from app.models.ai_analysis import AIAnalysis
from app.models.listing import Listing
from app.models.tracked_item import TrackedItem
from app.services.ai.analysis import AIAnalyzer
from app.services.ebay.poller import EbayPoller

_CANNED = json.dumps({
    "deal_grade": "buy", "reasoning": "ok", "scam_signal": False,
    "scam_reasons": [], "specs": {"cores": 24},
})


class _FakeClient:
    def __init__(self, enabled=True):
        self.enabled = enabled
        self.model = "fake-model"

    @property
    def is_enabled(self):
        return self.enabled

    async def complete(self, messages, **kwargs):
        return _CANNED


async def _add_item(db):
    item = TrackedItem(
        name="EPYC 7F72", keywords="EPYC 7F72", benchmark_median=350,
        scam_floor=10, search_interval=600, is_enabled=True,
    )
    db.add(item)
    await db.flush()
    return item


async def test_poll_path_runs_ai_when_enabled(db):
    item = await _add_item(db)
    poller = EbayPoller()
    poller.analyzer = AIAnalyzer(client=_FakeClient(enabled=True))

    result = await poller.search_item(db, item)
    await db.flush()

    analyses = (await db.execute(select(AIAnalysis).where(AIAnalysis.tracked_item_id == item.id))).scalars().all()
    assert result["new_listings"] >= 1
    assert len(analyses) == result["new_listings"]


async def test_poll_path_skips_ai_when_disabled(db):
    item = await _add_item(db)
    poller = EbayPoller()
    poller.analyzer = AIAnalyzer(client=_FakeClient(enabled=False))

    await poller.search_item(db, item)
    await db.flush()

    analyses = (await db.execute(select(AIAnalysis))).scalars().all()
    assert analyses == []


async def test_ai_endpoint_returns_latest_analysis(client, db):
    item = await _add_item(db)
    listing = Listing(
        marketplace_id="m1", tracked_item_id=item.id, title="x", price=100,
        shipping=0, seller="s", url="u", listing_date=datetime.utcnow(),
    )
    db.add(listing)
    await db.flush()
    db.add(AIAnalysis(
        listing_id=listing.id, tracked_item_id=item.id, provider="openrouter",
        model="m", deal_grade="strong buy", reasoning="r", scam_signal=False,
        scam_reasons=[], extracted_specs={"cores": 24},
    ))
    await db.flush()

    resp = await client.get(f"/api/v1/ai/{listing.id}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["analysis"]["deal_grade"] == "strong buy"
    assert body["analysis"]["extracted_specs"]["cores"] == 24


async def test_ai_endpoint_null_when_none(client, db):
    item = await _add_item(db)
    listing = Listing(
        marketplace_id="m2", tracked_item_id=item.id, title="x", price=100,
        shipping=0, seller="s", url="u2", listing_date=datetime.utcnow(),
    )
    db.add(listing)
    await db.flush()

    resp = await client.get(f"/api/v1/ai/{listing.id}")
    assert resp.status_code == 200
    assert resp.json()["analysis"] is None
