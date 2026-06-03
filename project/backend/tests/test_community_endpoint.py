"""feature-007 story-5: leads model + persistence + GET endpoint.

Proves the endpoint is auth-protected (via the shared `client` fixture's stub
user), filters by item_id/status, returns newest-first, reports a disabled state
when the gate is off, and that persistence dedups cross-run on
(source, source_post_id). No scoring/notification side effects.
"""
from datetime import datetime, timedelta

from sqlalchemy import select

from app.core.config import settings
from app.models.community_signal_lead import CommunitySignalLead
from app.models.tracked_item import TrackedItem
from app.services.community.persistence import persist_leads
from app.services.community.types import CommunityLead


async def _seed_item(db):
    item = TrackedItem(
        name="EPYC 7F72", keywords="EPYC 7F72", benchmark_median=350,
        scam_floor=10, search_interval=600, is_enabled=True,
    )
    db.add(item)
    await db.flush()
    return item


async def _seed_lead(db, post_id, *, status="for-sale", item_id=None, ingested=None):
    row = CommunitySignalLead(
        source="reddit_homelabsales", source_post_id=post_id,
        catalog_item_id=item_id, title=f"[H] EPYC {post_id}", url=f"http://x/{post_id}",
        model="EPYC 7F72", price=200, status=status,
    )
    if ingested is not None:
        row.ingested_at = ingested
    db.add(row)
    await db.flush()
    return row


async def test_leads_endpoint_returns_disabled_when_gate_off(client, db, monkeypatch):
    monkeypatch.setattr(settings, "ENABLE_COMMUNITY_SIGNAL", False)
    resp = await client.get("/api/v1/community-signal/leads")
    assert resp.status_code == 200
    body = resp.json()
    assert body["enabled"] is False
    assert body["leads"] == []
    assert body["count"] == 0


async def test_leads_endpoint_returns_rows_newest_first(client, db, monkeypatch):
    monkeypatch.setattr(settings, "ENABLE_COMMUNITY_SIGNAL", True)
    base = datetime(2026, 5, 1, 12, 0, 0)
    await _seed_lead(db, "p_old", ingested=base)
    await _seed_lead(db, "p_new", ingested=base + timedelta(hours=1))

    resp = await client.get("/api/v1/community-signal/leads")
    assert resp.status_code == 200
    body = resp.json()
    assert body["enabled"] is True
    assert body["count"] == 2
    assert body["leads"][0]["source_post_id"] == "p_new"


async def test_leads_endpoint_filters_by_item_and_status(client, db, monkeypatch):
    monkeypatch.setattr(settings, "ENABLE_COMMUNITY_SIGNAL", True)
    item = await _seed_item(db)
    await _seed_lead(db, "p1", item_id=item.id, status="for-sale")
    await _seed_lead(db, "p2", item_id=None, status="for-sale")
    await _seed_lead(db, "p3", item_id=item.id, status="unknown")

    resp = await client.get(f"/api/v1/community-signal/leads?item_id={item.id}")
    ids = {lead["source_post_id"] for lead in resp.json()["leads"]}
    assert ids == {"p1", "p3"}

    resp = await client.get("/api/v1/community-signal/leads?status=for-sale")
    ids = {lead["source_post_id"] for lead in resp.json()["leads"]}
    assert ids == {"p1", "p2"}


async def test_leads_endpoint_requires_auth(unauth_client, db, monkeypatch):
    monkeypatch.setattr(settings, "ENABLE_COMMUNITY_SIGNAL", True)
    resp = await unauth_client.get("/api/v1/community-signal/leads")
    assert resp.status_code == 401


async def test_persist_dedups_cross_run(db):
    lead = CommunityLead(
        source="reddit_homelabsales", source_post_id="dup1",
        title="[H] EPYC", url="http://x", model="EPYC 7F72", price=200, status="for-sale",
    )
    first = await persist_leads(db, [lead])
    assert len(first) == 1
    # Same post again -> no new row.
    second = await persist_leads(db, [lead])
    assert second == []
    rows = (await db.execute(select(CommunitySignalLead))).scalars().all()
    assert len(rows) == 1
