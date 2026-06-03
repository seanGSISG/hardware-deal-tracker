"""Sold/traded filter + in-run dedup for community leads (feature-007 story-4).

Runs BETWEEN extraction and persistence — never touches the scoring/notification
path. ``filter_stale`` drops leads whose extracted status (or whose post title
markers like [SOLD]/[TRADED]/CLOSED/PENDING) say the deal is gone. ``dedup_leads``
collapses repeats on (source, source_post_id) so the same post is never emitted
or persisted twice within a run; cross-run dedup is enforced by the table's
unique (source, source_post_id) constraint in persistence.
"""
from __future__ import annotations

import re

from app.services.community.types import CommunityLead

# Title markers that indicate a closed/gone deal even if the body status missed it.
_STALE_TITLE_RE = re.compile(
    r"\[\s*(sold|traded|closed|pending|complete[d]?)\s*\]|\b(sold|closed|pending)\b",
    re.IGNORECASE,
)


def _title_marks_stale(title: str | None) -> bool:
    if not title:
        return False
    return bool(_STALE_TITLE_RE.search(title))


def filter_stale(leads: list[CommunityLead]) -> list[CommunityLead]:
    """Keep only live for-sale/unknown leads; drop sold/traded/pending/closed."""
    live: list[CommunityLead] = []
    for lead in leads:
        if lead.is_stale or _title_marks_stale(lead.title):
            continue
        live.append(lead)
    return live


def dedup_leads(leads: list[CommunityLead]) -> list[CommunityLead]:
    """Collapse repeats on (source, source_post_id), keeping first occurrence."""
    seen: set[tuple[str, str]] = set()
    out: list[CommunityLead] = []
    for lead in leads:
        key = (lead.source, lead.source_post_id)
        if key in seen:
            continue
        seen.add(key)
        out.append(lead)
    return out
