"""feature-007 story-3: AIClient free-text lead extraction (LLM mocked).

TDD: written against captured r/homelabsales-style fixtures with a MOCKED
AIClient.complete() — zero network / zero live LLM. Proves the extractor parses
the structured fields, tolerates fenced ```json, degrades to None when disabled
or unparseable, and attaches catalog_item_id only when the model matches a
tracked item.
"""
import json
from pathlib import Path

from app.models.tracked_item import TrackedItem
from app.services.community.extractor import CommunityLeadExtractor
from app.services.community.types import CommunityPost

_FIXTURES = json.loads(
    (Path(__file__).parent / "fixtures" / "reddit_homelabsales_posts.json").read_text()
)


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


def _post(key: str) -> CommunityPost:
    raw = _FIXTURES[key]["post"]
    return CommunityPost(
        source=raw["source"], source_post_id=raw["source_post_id"],
        title=raw["title"], body=raw["body"], url=raw["url"], author=raw["author"],
    )


async def _seed_catalog(db):
    item = TrackedItem(
        name="EPYC 7F72", keywords="EPYC 7F72 AMD", benchmark_median=350,
        scam_floor=10, search_interval=600, is_enabled=True,
    )
    db.add(item)
    await db.flush()
    return item


async def test_extract_parses_fenced_json_and_fields(db):
    item = await _seed_catalog(db)
    fix = _FIXTURES["matches_catalog"]
    extractor = CommunityLeadExtractor(client=_FakeClient(fix["ai_response"]))

    lead = await extractor.extract(db, _post("matches_catalog"))
    assert lead is not None
    assert lead.model == "AMD EPYC 7F72"
    assert lead.price == 210.0
    assert lead.condition == "used"
    assert lead.location == "USA-CA"
    assert lead.status == "for-sale"
    assert lead.confidence == 0.92
    # Model matched the tracked catalog item.
    assert lead.catalog_item_id == item.id


async def test_extract_no_catalog_match_sets_none(db):
    await _seed_catalog(db)
    fix = _FIXTURES["no_catalog_match"]
    extractor = CommunityLeadExtractor(client=_FakeClient(fix["ai_response"]))

    lead = await extractor.extract(db, _post("no_catalog_match"))
    assert lead is not None
    assert lead.model == "Ubiquiti UniFi US-24-250W"
    assert lead.catalog_item_id is None


async def test_extract_disabled_returns_none(db):
    await _seed_catalog(db)
    fix = _FIXTURES["matches_catalog"]
    extractor = CommunityLeadExtractor(client=_FakeClient(fix["ai_response"], enabled=False))
    assert await extractor.extract(db, _post("matches_catalog")) is None


async def test_extract_unparseable_returns_none(db):
    await _seed_catalog(db)
    extractor = CommunityLeadExtractor(client=_FakeClient("not json at all"))
    assert await extractor.extract(db, _post("matches_catalog")) is None


async def test_extract_empty_content_returns_none(db):
    await _seed_catalog(db)
    extractor = CommunityLeadExtractor(client=_FakeClient(None))
    assert await extractor.extract(db, _post("matches_catalog")) is None
