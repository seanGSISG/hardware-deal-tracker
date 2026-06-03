"""Reddit r/homelabsales OAuth client (feature-007 story-2).

Obtains an OAuth2 token from https://www.reddit.com/api/v1/access_token (app-only
client_credentials by default; password grant when username/password are set),
then GET /r/<subreddit>/new from oauth.reddit.com, mapping each child into a
``CommunityPost``. Mirrors AIClient's defensive try/except-to-empty style: it
returns ``[]`` (never raises) when creds are missing or the API errors. Every
network call is recorded against the polite community rate bucket so it can never
eat eBay's 5000/day budget.

Nothing is hardcoded — all creds + the subreddit + user agent come from settings.
"""
from __future__ import annotations

import logging
from datetime import UTC, datetime

import httpx

from app.core.config import settings
from app.services.community.types import CommunityPost
from app.services.sources.rate_budget import SourceRateBudget

logger = logging.getLogger(__name__)

_TOKEN_URL = "https://www.reddit.com/api/v1/access_token"
_OAUTH_BASE = "https://oauth.reddit.com"


def reddit_creds_present() -> bool:
    """True when the minimum Reddit OAuth creds (id + secret) are configured."""
    return bool(settings.REDDIT_CLIENT_ID) and bool(settings.REDDIT_CLIENT_SECRET)


class RedditClient:
    def __init__(self, budget: SourceRateBudget, *, source_key: str):
        self.budget = budget
        self.source_key = source_key

    async def _get_token(self, client: httpx.AsyncClient) -> str | None:
        if not reddit_creds_present():
            return None
        if settings.REDDIT_USERNAME and settings.REDDIT_PASSWORD:
            data = {
                "grant_type": "password",
                "username": settings.REDDIT_USERNAME,
                "password": settings.REDDIT_PASSWORD,
            }
        else:
            # App-only (installed-client) grant.
            data = {"grant_type": "client_credentials"}
        resp = await client.post(
            _TOKEN_URL,
            data=data,
            auth=(settings.REDDIT_CLIENT_ID, settings.REDDIT_CLIENT_SECRET),
            headers={"User-Agent": settings.REDDIT_USER_AGENT},
        )
        resp.raise_for_status()
        return resp.json().get("access_token")

    @staticmethod
    def _map_child(child: dict) -> CommunityPost | None:
        data = (child or {}).get("data") or {}
        post_id = data.get("name") or data.get("id")
        if not post_id:
            return None
        created = data.get("created_utc")
        created_at = (
            datetime.fromtimestamp(created, tz=UTC)
            if isinstance(created, (int, float))
            else None
        )
        permalink = data.get("permalink")
        url = f"https://www.reddit.com{permalink}" if permalink else (data.get("url") or "")
        return CommunityPost(
            source="reddit_homelabsales",
            source_post_id=str(post_id),
            title=data.get("title") or "",
            body=data.get("selftext") or "",
            url=url,
            author=data.get("author"),
            created_at=created_at,
            raw=data,
        )

    async def fetch_new(self, *, limit: int = 50) -> list[CommunityPost]:
        """Fetch the newest posts; returns [] (never raises) on any failure."""
        if not reddit_creds_present():
            logger.debug("reddit creds absent; community fetch is a no-op")
            return []
        if not self.budget.can_call(self.source_key):
            logger.warning("community rate bucket exhausted; skipping reddit fetch")
            return []
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                token = await self._get_token(client)
                if not token:
                    return []
                self.budget.record_call(self.source_key)
                resp = await client.get(
                    f"{_OAUTH_BASE}/r/{settings.REDDIT_SUBREDDIT}/new",
                    params={"limit": limit},
                    headers={
                        "Authorization": f"Bearer {token}",
                        "User-Agent": settings.REDDIT_USER_AGENT,
                    },
                )
                resp.raise_for_status()
                children = (resp.json().get("data") or {}).get("children") or []
        except Exception:
            logger.exception("reddit community fetch failed; degrading to []")
            return []

        posts = [p for p in (self._map_child(c) for c in children) if p is not None]
        return posts
