"""Persist surviving community leads (feature-007 story-5).

Writes leads to the ``community_signal_leads`` table only. Cross-run dedup is
enforced here by skipping any (source, source_post_id) already present, mirroring
the unique constraint on the table. NEVER touches ListingScore / PriceHistory /
Notification — this is a separate surface (ADR-007).
"""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.community_signal_lead import CommunitySignalLead
from app.services.community.types import CommunityLead


async def persist_leads(
    db: AsyncSession, leads: list[CommunityLead]
) -> list[CommunitySignalLead]:
    """Insert new leads, skipping any (source, source_post_id) already stored."""
    if not leads:
        return []

    keys = {(lead.source, lead.source_post_id) for lead in leads}
    existing = set(
        (
            await db.execute(
                select(
                    CommunitySignalLead.source, CommunitySignalLead.source_post_id
                ).where(
                    CommunitySignalLead.source_post_id.in_(
                        [k[1] for k in keys]
                    )
                )
            )
        ).all()
    )

    rows: list[CommunitySignalLead] = []
    for lead in leads:
        if (lead.source, lead.source_post_id) in existing:
            continue
        existing.add((lead.source, lead.source_post_id))
        row = CommunitySignalLead(
            source=lead.source,
            source_post_id=lead.source_post_id,
            catalog_item_id=lead.catalog_item_id,
            title=lead.title,
            url=lead.url,
            author=lead.author,
            model=lead.model,
            price=lead.price,
            condition=lead.condition,
            location=lead.location,
            status=lead.status,
            confidence=lead.confidence,
            ai_reason=lead.ai_reason,
            raw_payload=lead.raw or None,
            posted_at=lead.posted_at,
        )
        db.add(row)
        rows.append(row)

    if rows:
        await db.flush()
    return rows
