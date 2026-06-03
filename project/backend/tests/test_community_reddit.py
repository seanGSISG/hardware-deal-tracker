"""feature-007 story-2: Reddit r/homelabsales OAuth client.

The single live round-trip is `community_live`-marked + skipif-gated on creds, so
it SKIPS cleanly by default (CI excludes it like real_ebay/live_smoke). The
unit-level tests below need no network: they prove the client degrades to [] when
creds are absent and that the listing->CommunityPost mapping is correct.
"""
import os

import pytest

from app.core.config import settings
from app.services.community.reddit import RedditClient, reddit_creds_present
from app.services.community.source import COMMUNITY_SOURCE_KEY
from app.services.sources.rate_budget import SourceRateBudget


def _reddit_ready() -> bool:
    return bool(os.getenv("REDDIT_CLIENT_ID")) and bool(os.getenv("REDDIT_CLIENT_SECRET"))


def test_community_live_marker_is_registered(pytestconfig):
    markers = pytestconfig.getini("markers")
    assert any(m.startswith("community_live:") for m in markers), (
        "community_live marker must be registered in pyproject.toml"
    )


def test_creds_gate_reports_not_ready_without_creds(monkeypatch):
    monkeypatch.setattr(settings, "REDDIT_CLIENT_ID", "")
    monkeypatch.setattr(settings, "REDDIT_CLIENT_SECRET", "")
    assert reddit_creds_present() is False


async def test_fetch_degrades_to_empty_without_creds(monkeypatch):
    monkeypatch.setattr(settings, "REDDIT_CLIENT_ID", "")
    monkeypatch.setattr(settings, "REDDIT_CLIENT_SECRET", "")
    budget = SourceRateBudget(default_daily_limit=settings.COMMUNITY_SIGNAL_DAILY_LIMIT)
    client = RedditClient(budget, source_key=COMMUNITY_SOURCE_KEY)
    # Must NOT raise and must NOT make any network call.
    posts = await client.fetch_new(limit=10)
    assert posts == []
    # No call recorded against the bucket (we short-circuited before the network).
    assert budget.status(COMMUNITY_SOURCE_KEY)["calls_today"] == 0


def test_map_child_builds_community_post():
    child = {
        "data": {
            "name": "t3_abc123",
            "title": "[USA-CA][H] AMD EPYC 7F72 [W] PayPal",
            "selftext": "Selling EPYC 7F72, used, $200 shipped.",
            "permalink": "/r/homelabsales/comments/abc123/x/",
            "author": "seller42",
            "created_utc": 1_700_000_000,
        }
    }
    post = RedditClient._map_child(child)
    assert post is not None
    assert post.source == "reddit_homelabsales"
    assert post.source_post_id == "t3_abc123"
    assert "EPYC 7F72" in post.title
    assert post.url.endswith("/r/homelabsales/comments/abc123/x/")
    assert post.author == "seller42"
    assert post.created_at is not None


def test_map_child_skips_missing_id():
    assert RedditClient._map_child({"data": {}}) is None


@pytest.mark.community_live
@pytest.mark.skipif(not _reddit_ready(), reason="Reddit creds not set")
async def test_reddit_live_round_trip():
    budget = SourceRateBudget(default_daily_limit=settings.COMMUNITY_SIGNAL_DAILY_LIMIT)
    client = RedditClient(budget, source_key=COMMUNITY_SOURCE_KEY)
    posts = await client.fetch_new(limit=5)
    # Live subreddit should yield at least one post; each maps cleanly.
    assert isinstance(posts, list)
    for p in posts:
        assert p.source_post_id
        assert p.source == "reddit_homelabsales"
