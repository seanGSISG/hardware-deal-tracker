"""feature-007 story-1: CommunitySignalSource gate + polite rate bucket.

TDD: written FIRST. Proves the ingest entrypoint is a pure no-op when
ENABLE_COMMUNITY_SIGNAL is False (zero network, zero AI work) and that the
source uses a community-specific rate bucket key distinct from eBay's budget.
"""
import app.services.community.source as source_mod
from app.core.config import settings
from app.services.community.source import COMMUNITY_SOURCE_KEY, CommunitySignalSource
from app.services.community.types import CommunityLead, CommunityPost


def test_dataclasses_have_expected_shape():
    post = CommunityPost(
        source="reddit_homelabsales", source_post_id="t3_abc",
        title="[USA-CA][H] EPYC 7F72 [W] PayPal", body="200 shipped", url="http://x",
    )
    assert post.source == "reddit_homelabsales"
    lead = CommunityLead(
        source="reddit_homelabsales", source_post_id="t3_abc",
        title=post.title, url=post.url, model="EPYC 7F72", price=200.0, status="for-sale",
    )
    assert lead.catalog_item_id is None
    assert lead.is_stale is False


def test_rate_bucket_key_is_community_specific():
    src = CommunitySignalSource()
    assert COMMUNITY_SOURCE_KEY.startswith("reddit")
    # The community bucket must not be eBay's 5000/day limit.
    assert src.budget.status(COMMUNITY_SOURCE_KEY)["daily_limit"] != 5000
    assert src.budget.status(COMMUNITY_SOURCE_KEY)["daily_limit"] == settings.COMMUNITY_SIGNAL_DAILY_LIMIT


async def test_ingest_is_noop_when_gate_off(db, monkeypatch):
    monkeypatch.setattr(settings, "ENABLE_COMMUNITY_SIGNAL", False)

    # Guard: fetching/extraction must never be invoked while the gate is off.
    def _boom(*a, **k):  # pragma: no cover - asserts it is never called
        raise AssertionError("network/AI must not run when the gate is off")

    monkeypatch.setattr(source_mod, "RedditClient", lambda *a, **k: _boom())

    src = CommunitySignalSource()
    leads = await src.ingest(db)
    assert leads == []


async def test_ingest_runs_when_gate_on_with_injected_fetcher(db, monkeypatch):
    monkeypatch.setattr(settings, "ENABLE_COMMUNITY_SIGNAL", True)

    post = CommunityPost(
        source="reddit_homelabsales", source_post_id="t3_1",
        title="[USA][H] EPYC [W] PayPal", body="EPYC 7F72, $200 shipped, used",
        url="http://x", author="seller",
    )

    async def _fake_fetch(self):
        self.budget.record_call(COMMUNITY_SOURCE_KEY)
        return [post]

    async def _fake_extract(self, db, p):
        return CommunityLead(
            source=p.source, source_post_id=p.source_post_id, title=p.title,
            url=p.url, model="EPYC 7F72", price=200.0, status="for-sale",
        )

    monkeypatch.setattr(CommunitySignalSource, "_fetch_posts", _fake_fetch)
    monkeypatch.setattr(CommunitySignalSource, "_extract", _fake_extract)

    src = CommunitySignalSource()
    leads = await src.ingest(db)
    assert len(leads) == 1
    assert leads[0].model == "EPYC 7F72"
    # The call went through the community bucket.
    assert src.budget.status(COMMUNITY_SOURCE_KEY)["calls_today"] >= 1
