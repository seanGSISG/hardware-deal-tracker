"""story-T2.5: lock down /auth/register and make PUT /settings/notifications upsert."""
import pytest

from app.core.config import settings
from app.models.notification_setting import NotificationSetting
from app.models.user import User


@pytest.fixture(autouse=True)
async def _seed_current_user(db):
    """Persist the stub user (id=1) the `client` fixture authenticates as.

    Settings rows FK to users.id; create the row so upsert has a valid owner.
    """
    db.add(User(id=1, username="tester", email="tester@example.com", hashed_password="x", is_active=True))
    await db.flush()


async def test_register_blocked_when_disabled(client, monkeypatch):
    monkeypatch.setattr(settings, "ALLOW_REGISTRATION", False)
    resp = await client.post(
        "/api/v1/auth/register",
        json={"username": "newuser", "email": "new@example.com", "password": "supersecret"},
    )
    assert resp.status_code == 403


async def test_register_allowed_when_enabled(client, monkeypatch):
    monkeypatch.setattr(settings, "ALLOW_REGISTRATION", True)
    resp = await client.post(
        "/api/v1/auth/register",
        json={"username": "newuser", "email": "new@example.com", "password": "supersecret"},
    )
    assert resp.status_code == 200
    assert resp.json()["access_token"]


async def test_put_notifications_upserts_when_missing(client, db):
    # No settings row exists yet for the user -> PUT must create one, not 404.
    resp = await client.put(
        "/api/v1/settings/notifications",
        json={"telegram_min_score": 80, "email_enabled": False},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["telegram_min_score"] == 80
    assert body["email_enabled"] is False

    rows = (await db.execute(NotificationSetting.__table__.select())).fetchall()
    assert len(rows) == 1


async def test_put_notifications_updates_existing(client, db):
    db.add(NotificationSetting(user_id=1, telegram_min_score=70))
    await db.flush()

    resp = await client.put(
        "/api/v1/settings/notifications",
        json={"telegram_min_score": 90},
    )
    assert resp.status_code == 200
    assert resp.json()["telegram_min_score"] == 90
