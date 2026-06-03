"""User-managed catalog CRUD is admin-gated.

Write operations on tracked items (create/update/delete/toggle/bulk-update)
require an admin user. Reads remain open to any authenticated user. This lets
non-admins browse the catalog while only admins mutate it.
"""
def _item_payload(name="Test Widget"):
    return {
        "name": name,
        "keywords": f"{name} keywords",
        "category_id": "56083",
        "target_price": 100.0,
        "benchmark_median": 150.0,
        "scam_floor": 50.0,
        "search_interval": 600,
        "alert_threshold": 0.2,
        "min_deal_score": 55,
        "is_enabled": True,
    }


async def test_non_admin_cannot_create_item(client):
    resp = await client.post("/api/v1/items", json=_item_payload())
    assert resp.status_code == 403


async def test_admin_can_create_item(admin_client):
    resp = await admin_client.post("/api/v1/items", json=_item_payload("Admin Widget"))
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["name"] == "Admin Widget"
    assert body["id"] > 0


async def test_non_admin_can_still_read_items(client):
    resp = await client.get("/api/v1/items")
    assert resp.status_code == 200


async def test_admin_full_crud_roundtrip(admin_client):
    # Create
    create = await admin_client.post("/api/v1/items", json=_item_payload("Roundtrip"))
    assert create.status_code == 200, create.text
    item_id = create.json()["id"]

    # Update
    upd = await admin_client.put(
        f"/api/v1/items/{item_id}", json={"target_price": 88.0, "is_enabled": False}
    )
    assert upd.status_code == 200, upd.text
    assert float(upd.json()["target_price"]) == 88.0

    # Delete
    dele = await admin_client.delete(f"/api/v1/items/{item_id}")
    assert dele.status_code == 200, dele.text


async def test_non_admin_cannot_update_or_delete(db, client):
    # Seed an item directly via the shared db session (no admin client needed,
    # avoiding dependency-override collisions between fixtures).
    from app.models.tracked_item import TrackedItem

    item = TrackedItem(name="Locked", keywords="locked kw", search_interval=600)
    db.add(item)
    await db.flush()
    item_id = item.id

    upd = await client.put(f"/api/v1/items/{item_id}", json={"target_price": 1.0})
    assert upd.status_code == 403

    dele = await client.delete(f"/api/v1/items/{item_id}")
    assert dele.status_code == 403


async def test_non_admin_cannot_toggle_or_bulk_update(client):
    toggle = await client.put("/api/v1/items/1/toggle")
    assert toggle.status_code == 403

    bulk = await client.post("/api/v1/items/bulk-update", json={"ids": [1], "action": "disable"})
    assert bulk.status_code == 403
