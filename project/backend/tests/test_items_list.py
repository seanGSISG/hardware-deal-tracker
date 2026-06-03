"""T3.4 — GET /items uses a response_model whose priority_tier is a computed_field.

Replaces the hand-rolled `_serialize_item` dict helper: the list endpoint now
returns a typed, validated payload where priority_tier is derived from
search_interval by a Pydantic v2 @computed_field (single source of truth).
"""
from app.models.tracked_item import TrackedItem
from app.schemas.tracked_item import TrackedItemListEntry


async def _add(db, name, interval):
    item = TrackedItem(name=name, keywords=name, search_interval=interval, is_enabled=True)
    db.add(item)
    await db.flush()
    return item


def test_computed_priority_tier_buckets():
    # The schema computes priority_tier from search_interval, not a stored column.
    assert TrackedItemListEntry.model_construct(search_interval=300).priority_tier == "P0"
    entry = TrackedItemListEntry(
        id=1, name="x", keywords="x", search_interval=300,
        created_at="2026-01-01T00:00:00Z", updated_at="2026-01-01T00:00:00Z",
    )
    assert "priority_tier" in entry.model_dump()
    assert entry.priority_tier == "P0"
    for interval, tier in [(360, "P0"), (600, "P1"), (1200, "P2"), (1800, "P3")]:
        e = TrackedItemListEntry(
            id=1, name="x", keywords="x", search_interval=interval,
            created_at="2026-01-01T00:00:00Z", updated_at="2026-01-01T00:00:00Z",
        )
        assert e.priority_tier == tier


async def test_list_items_returns_priority_tier_and_image(client, db):
    await _add(db, "EPYC 7F72", 300)
    await _add(db, "NVIDIA T4 16GB", 1800)

    resp = await client.get("/api/v1/items")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 2
    tiers = {item["name"]: item["priority_tier"] for item in body["items"]}
    assert tiers["EPYC 7F72"] == "P0"
    assert tiers["NVIDIA T4 16GB"] == "P3"
    # latest_image_url still present (None when no listings yet).
    assert all("latest_image_url" in item for item in body["items"])
