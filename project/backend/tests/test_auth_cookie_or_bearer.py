"""story-T2.2: get_current_user resolves a JWT from EITHER the session cookie OR
the Authorization: Bearer header. Missing both -> 401. Bearer-only must not regress.
"""
from app.core.security import create_access_token
from app.models.user import User


async def _seed_user(db, user_id=42):
    user = User(
        id=user_id, username=f"u{user_id}", email=f"u{user_id}@example.com",
        hashed_password="x", is_active=True,
    )
    db.add(user)
    await db.flush()
    return user


async def test_cookie_only_auth_reaches_protected_route(unauth_client, db):
    await _seed_user(db, 42)
    token = create_access_token({"sub": "42"})
    unauth_client.cookies.set("session", token)
    resp = await unauth_client.get("/api/v1/items")
    unauth_client.cookies.clear()
    assert resp.status_code == 200
    assert "items" in resp.json()


async def test_bearer_only_auth_still_works(unauth_client, db):
    await _seed_user(db, 43)
    token = create_access_token({"sub": "43"})
    resp = await unauth_client.get(
        "/api/v1/items", headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 200
    assert "items" in resp.json()


async def test_neither_cookie_nor_bearer_is_401(unauth_client, db):
    resp = await unauth_client.get("/api/v1/items")
    assert resp.status_code in (401, 403)


async def test_invalid_cookie_token_is_401(unauth_client, db):
    unauth_client.cookies.set("session", "not-a-jwt")
    resp = await unauth_client.get("/api/v1/items")
    unauth_client.cookies.clear()
    assert resp.status_code == 401


async def test_bearer_preferred_when_cookie_invalid(unauth_client, db):
    """A valid bearer must succeed even if a stale/invalid cookie is also present."""
    await _seed_user(db, 44)
    token = create_access_token({"sub": "44"})
    unauth_client.cookies.set("session", "stale-invalid-cookie")
    resp = await unauth_client.get(
        "/api/v1/items", headers={"Authorization": f"Bearer {token}"}
    )
    unauth_client.cookies.clear()
    assert resp.status_code == 200
