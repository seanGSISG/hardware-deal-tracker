"""Free-text lead extraction via the existing AIClient (feature-007 story-3).

Builds a system+user prompt and calls ``AIClient.complete()`` to turn a
``CommunityPost`` body into a structured ``CommunityLead``. Parsing tolerates
fenced ```json responses (mirrors AIAnalyzer._parse). Degrades to None when AI is
disabled, returns nothing, or content is unparseable — so the orchestrator simply
skips that post and never errors.

When a ``db`` session is supplied, the parsed model is best-effort matched
against tracked catalog items to populate ``catalog_item_id`` (None when no
match). Matching is a cheap keyword/name overlap — it never routes through the
scoring pipeline.
"""
from __future__ import annotations

import json
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tracked_item import TrackedItem
from app.services.ai.client import AIClient
from app.services.community.types import LEAD_STATUSES, CommunityLead, CommunityPost

logger = logging.getLogger(__name__)

_SYSTEM = (
    "You extract structured deal data from a homelab marketplace post (e.g. "
    "Reddit r/homelabsales). Respond ONLY with a compact JSON object with keys: "
    "model (string: the hardware model/part being sold, or null), "
    "price (number in USD, or null), "
    "condition (short string e.g. new/used/refurbished, or null), "
    "location (short string e.g. 'USA-CA', or null), "
    "status (one of: for-sale, sold, traded, pending, unknown), "
    "confidence (number 0..1), reason (short string). "
    "Do not include any prose outside the JSON."
)


def build_extraction_messages(post: CommunityPost) -> list[dict]:
    facts = {"title": post.title, "body": post.body}
    return [
        {"role": "system", "content": _SYSTEM},
        {"role": "user", "content": json.dumps(facts)},
    ]


def _parse(content: str) -> dict | None:
    """Parse the model's JSON, tolerating ```json fenced responses."""
    text = content.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:]
    try:
        data = json.loads(text)
        return data if isinstance(data, dict) else None
    except (ValueError, TypeError):
        return None


def _normalize_status(value) -> str:
    status = str(value or "unknown").strip().lower()
    return status if status in LEAD_STATUSES else "unknown"


def _coerce_price(value) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


class CommunityLeadExtractor:
    def __init__(self, client: AIClient | None = None):
        self.client = client or AIClient()

    @property
    def is_enabled(self) -> bool:
        return self.client.is_enabled

    async def _match_catalog_item_id(
        self, db: AsyncSession | None, model: str | None
    ) -> int | None:
        """Best-effort match the parsed model to a tracked catalog item id."""
        if db is None or not model:
            return None
        needle = model.strip().lower()
        if not needle:
            return None
        rows = (
            await db.execute(select(TrackedItem.id, TrackedItem.name, TrackedItem.keywords))
        ).all()
        for row in rows:
            name = (row.name or "").lower()
            keywords = (row.keywords or "").lower()
            if name and (name in needle or needle in name):
                return row.id
            # Keyword overlap: any catalog keyword token present in the model text.
            for token in keywords.replace(",", " ").split():
                if len(token) >= 3 and token in needle:
                    return row.id
        return None

    async def extract(
        self, db: AsyncSession | None, post: CommunityPost
    ) -> CommunityLead | None:
        if not self.client.is_enabled:
            return None
        messages = build_extraction_messages(post)
        content = await self.client.complete(messages)
        if not content:
            return None
        parsed = _parse(content)
        if parsed is None:
            logger.warning(
                "community extraction unparseable for post %s", post.source_post_id
            )
            return None

        model = parsed.get("model")
        catalog_item_id = await self._match_catalog_item_id(db, model)
        return CommunityLead(
            source=post.source,
            source_post_id=post.source_post_id,
            title=post.title,
            url=post.url,
            author=post.author,
            catalog_item_id=catalog_item_id,
            model=model,
            price=_coerce_price(parsed.get("price")),
            condition=parsed.get("condition"),
            location=parsed.get("location"),
            status=_normalize_status(parsed.get("status")),
            confidence=_coerce_price(parsed.get("confidence")),
            ai_reason=parsed.get("reason"),
            posted_at=post.created_at,
            raw=post.raw,
        )
