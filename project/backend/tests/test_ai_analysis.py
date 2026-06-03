"""story-4 (feature-006): AI analyses (deal grade, scam signal, spec extraction)."""
import json
from datetime import datetime

from sqlalchemy import select

from app.models.ai_analysis import AIAnalysis
from app.models.listing import Listing
from app.models.tracked_item import TrackedItem
from app.services.ai.analysis import AIAnalyzer, build_analysis_messages


class _FakeClient:
    def __init__(self, content, enabled=True):
        self._content = content
        self.enabled = enabled
        self.model = "fake-model"
        self.calls = []

    @property
    def is_enabled(self):
        return self.enabled

    async def complete(self, messages, **kwargs):
        self.calls.append(messages)
        return self._content


_CANNED = json.dumps({
    "deal_grade": "strong buy",
    "reasoning": "22% under 90d median, reputable seller",
    "scam_signal": True,
    "scam_reasons": ["price far below floor", "vague specs"],
    "specs": {"cores": 24, "tdp": 240, "socket": "SP3"},
})


async def _seed(db):
    item = TrackedItem(
        name="EPYC 7F72", keywords="EPYC 7F72", benchmark_median=350,
        scam_floor=10, search_interval=600, is_enabled=True,
    )
    db.add(item)
    await db.flush()
    listing = Listing(
        marketplace_id="m1", tracked_item_id=item.id, title="AMD EPYC 7F72 24-core",
        price=250, shipping=0, seller="seller", url="u", listing_date=datetime.utcnow(),
    )
    db.add(listing)
    await db.flush()
    return item, listing


async def test_build_messages_includes_listing_facts(db):
    item, listing = await _seed(db)
    messages = build_analysis_messages(listing, item)
    blob = json.dumps(messages)
    assert "EPYC 7F72" in blob
    assert "250" in blob  # price surfaced to the model


async def test_analyze_persists_ai_analysis(db):
    item, listing = await _seed(db)
    analyzer = AIAnalyzer(client=_FakeClient(_CANNED))

    result = await analyzer.analyze_listing(db, listing, catalog_item=item)
    await db.flush()

    assert result is not None
    rows = (await db.execute(select(AIAnalysis).where(AIAnalysis.listing_id == listing.id))).scalars().all()
    assert len(rows) == 1
    row = rows[0]
    assert row.deal_grade == "strong buy"
    assert row.scam_signal is True
    assert "vague specs" in row.scam_reasons
    assert row.extracted_specs["cores"] == 24
    assert row.model == "fake-model"


async def test_analyze_disabled_returns_none_and_persists_nothing(db):
    item, listing = await _seed(db)
    analyzer = AIAnalyzer(client=_FakeClient(_CANNED, enabled=False))

    result = await analyzer.analyze_listing(db, listing, catalog_item=item)
    await db.flush()

    assert result is None
    rows = (await db.execute(select(AIAnalysis))).scalars().all()
    assert rows == []


async def test_analyze_malformed_json_degrades_gracefully(db):
    item, listing = await _seed(db)
    analyzer = AIAnalyzer(client=_FakeClient("not json at all"))

    result = await analyzer.analyze_listing(db, listing, catalog_item=item)
    assert result is None
