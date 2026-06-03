"""Read-only 'similar tracked items' endpoint (feature-006, story-4, ADR-006).

OPTIONAL semantic affordance. When ENABLE_SEMANTIC_MATCHING + AI are on it
returns the top-N tracked items most similar to the given item by embedding
cosine similarity. When the feature is disabled (the default) or AI is off it
returns a clean, documented {"enabled": false, "similar": []} shape — never a
500 and without triggering any pgvector-dependent path.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.core.config import settings
from app.models.tracked_item import TrackedItem
from app.models.user import User
from app.services.semantic.matcher import SemanticMatcher

router = APIRouter(prefix="/semantic", tags=["semantic"])


@router.get("/similar/{item_id}")
async def get_similar_items(
    item_id: int,
    top_n: int = Query(default=None, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Top-N tracked items similar to ``item_id`` (or a disabled/empty shape)."""
    matcher = SemanticMatcher(db)
    # Short-circuit when off so no embedding/pgvector path is ever reached.
    if not matcher.is_enabled:
        return {"enabled": False, "item_id": item_id, "similar": []}

    item = await db.get(TrackedItem, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")

    ranked = await matcher.similar_items(item, top_n or settings.SEMANTIC_SIMILAR_TOP_N)
    return {
        "enabled": True,
        "item_id": item_id,
        "similar": [
            {"id": it.id, "name": it.name, "similarity": round(score, 6)}
            for it, score in ranked
        ],
    }
