"""Community-signal leads endpoint (feature-007, ADR-007).

GET /api/v1/community-signal/leads — auth-protected, newest-first, optional
item_id + status filters. Reads ONLY the leads table; never the scored-listing
pipeline. When ENABLE_COMMUNITY_SIGNAL is off the endpoint reports a disabled
state with an empty list instead of touching the DB-backed feature.
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.core.config import settings
from app.models.community_signal_lead import CommunitySignalLead
from app.models.user import User

router = APIRouter(prefix="/community-signal", tags=["community-signal"])


def _serialize(row: CommunitySignalLead) -> dict:
    return {
        "id": row.id,
        "source": row.source,
        "source_post_id": row.source_post_id,
        "catalog_item_id": row.catalog_item_id,
        "title": row.title,
        "url": row.url,
        "author": row.author,
        "model": row.model,
        "price": float(row.price) if row.price is not None else None,
        "condition": row.condition,
        "location": row.location,
        "status": row.status,
        "confidence": float(row.confidence) if row.confidence is not None else None,
        "ai_reason": row.ai_reason,
        "posted_at": row.posted_at.isoformat() if row.posted_at else None,
        "ingested_at": row.ingested_at.isoformat() if row.ingested_at else None,
    }


@router.get("/leads")
async def list_community_leads(
    item_id: int | None = Query(default=None),
    status: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """List community leads (newest first). Reports disabled when the gate is off."""
    if not settings.ENABLE_COMMUNITY_SIGNAL:
        return {"enabled": False, "count": 0, "leads": []}

    stmt = select(CommunitySignalLead)
    if item_id is not None:
        stmt = stmt.where(CommunitySignalLead.catalog_item_id == item_id)
    if status:
        stmt = stmt.where(CommunitySignalLead.status == status)
    stmt = stmt.order_by(
        CommunitySignalLead.ingested_at.desc(), CommunitySignalLead.id.desc()
    ).limit(limit)

    rows = (await db.execute(stmt)).scalars().all()
    return {"enabled": True, "count": len(rows), "leads": [_serialize(r) for r in rows]}
