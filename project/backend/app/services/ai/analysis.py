"""AI deal analysis (feature-006): grade, scam signal, and spec extraction.

One LLM call per listing returns a structured JSON verdict that is parsed and
persisted as an AIAnalysis row. Text-only (no vision). Fully optional: when the
provider is disabled or returns nothing parseable, analyze_listing returns None
and persists nothing, so the poll/score path is never blocked.
"""
import json
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.ai_analysis import AIAnalysis
from app.models.listing import Listing
from app.services.ai.client import AIClient

logger = logging.getLogger(__name__)

_SYSTEM = (
    "You are an enterprise-hardware deal analyst. Given one marketplace listing, "
    "respond ONLY with a compact JSON object with keys: "
    "deal_grade (one of: strong buy, buy, fair, pass), "
    "reasoning (short string), "
    "scam_signal (boolean: true if the text shows fraud/too-good-to-be-true/vague-spec/"
    "drop-ship signals), scam_reasons (array of short strings), "
    "specs (object of structured specs parsed from the title/description, e.g. "
    "cores, tdp, socket, capacity). Do not include any prose outside the JSON."
)


def build_analysis_messages(listing: Listing, catalog_item=None) -> list[dict]:
    facts = {
        "title": listing.title,
        "price": float(listing.price),
        "shipping": float(listing.shipping),
        "total": float(listing.price) + float(listing.shipping),
        "condition": listing.condition,
        "seller": listing.seller,
        "seller_feedback": listing.seller_feedback,
    }
    if catalog_item is not None:
        facts["catalog_item"] = catalog_item.name
        facts["benchmark_median"] = (
            float(catalog_item.benchmark_median) if catalog_item.benchmark_median is not None else None
        )
        facts["scam_floor"] = (
            float(catalog_item.scam_floor) if catalog_item.scam_floor is not None else None
        )
    return [
        {"role": "system", "content": _SYSTEM},
        {"role": "user", "content": json.dumps(facts)},
    ]


def _parse(content: str) -> dict | None:
    text = content.strip()
    # Tolerate ```json ... ``` fenced responses.
    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:]
    try:
        data = json.loads(text)
        return data if isinstance(data, dict) else None
    except (ValueError, TypeError):
        return None


class AIAnalyzer:
    def __init__(self, client: AIClient | None = None):
        self.client = client or AIClient()

    @property
    def is_enabled(self) -> bool:
        return self.client.is_enabled

    async def analyze_listing(
        self, db: AsyncSession, listing: Listing, catalog_item=None
    ) -> AIAnalysis | None:
        if not self.client.is_enabled:
            return None
        messages = build_analysis_messages(listing, catalog_item)
        content = await self.client.complete(messages)
        if not content:
            return None
        parsed = _parse(content)
        if parsed is None:
            logger.warning("AI analysis returned unparseable content for listing %s", listing.id)
            return None

        row = AIAnalysis(
            listing_id=listing.id,
            tracked_item_id=getattr(catalog_item, "id", None),
            provider=settings.AI_PROVIDER,
            model=self.client.model,
            deal_grade=parsed.get("deal_grade"),
            reasoning=parsed.get("reasoning"),
            scam_signal=bool(parsed.get("scam_signal", False)),
            scam_reasons=parsed.get("scam_reasons"),
            extracted_specs=parsed.get("specs"),
        )
        db.add(row)
        await db.flush()
        return row
