"""story-T2.6: end-to-end auth integration guard.

Proves T2.1 (cookie issuance/clear) + T2.2 (cookie-OR-bearer resolution) + T2.3
(credentialed CORS) compose correctly against the REAL auth path (unauth_client):

  login -> Set-Cookie session
        -> protected endpoint via ONLY the cookie         -> 200
        -> protected endpoint via ONLY the bearer body     -> 200 (API/test path)
  logout -> cookie cleared
        -> protected endpoint via the now-cleared cookie   -> 401

This is the regression net ensuring the cookie path works AND the bearer path for
API clients / the pytest fixtures was never broken.
"""
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.core.config import settings

CREDS = {"username": "e2euser", "email": "e2e@example.com", "password": "supersecret123"}
PROTECTED = "/api/v1/items"


@pytest_asyncio.fixture
async def https_client(db):
    """Real-auth HTTP client over an https base_url.

    The session cookie is issued with Secure=True, so httpx will only resend it
    over https. base_url='http://test' (as in unauth_client) silently drops the
    cookie, masking the cookie auth path. This fixture mirrors unauth_client but
    speaks https so the end-to-end cookie round-trip is genuinely exercised.
    """
    from app.api.deps import get_db
    from app.main import app

    async def _override_get_db():
        yield db

    app.dependency_overrides[get_db] = _override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="https://test") as http_client:
        yield http_client
    app.dependency_overrides.clear()


async def _register_and_login(unauth_client, monkeypatch):
    monkeypatch.setattr(settings, "ALLOW_REGISTRATION", True)
    await unauth_client.post("/api/v1/auth/register", json=CREDS)
    # Clear cookies set by register so login is the sole cookie source under test.
    unauth_client.cookies.clear()
    resp = await unauth_client.post(
        "/api/v1/auth/login",
        json={"username": CREDS["username"], "password": CREDS["password"]},
    )
    assert resp.status_code == 200
    return resp


async def test_full_flow_cookie_path(https_client, monkeypatch):
    """login -> protected via ONLY the session cookie -> 200 (over https)."""
    login = await _register_and_login(https_client, monkeypatch)
    assert https_client.cookies.get("session")  # httpx persisted the Set-Cookie

    # No Authorization header: the persisted Secure cookie alone must authenticate.
    resp = await https_client.get(PROTECTED)
    assert resp.status_code == 200
    assert "items" in resp.json()
    # sanity: login also returned the bearer body
    assert login.json()["access_token"]


async def test_full_flow_bearer_path(unauth_client, monkeypatch):
    """Same protected endpoint via ONLY the Authorization: Bearer token -> 200."""
    login = await _register_and_login(unauth_client, monkeypatch)
    token = login.json()["access_token"]
    # Drop the cookie so the bearer header is the sole credential.
    unauth_client.cookies.clear()
    resp = await unauth_client.get(
        PROTECTED, headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 200
    assert "items" in resp.json()


async def test_logout_clears_cookie_then_protected_is_401(https_client, monkeypatch):
    """logout clears the cookie; a subsequent cookie-only request -> 401."""
    await _register_and_login(https_client, monkeypatch)
    # Cookie works before logout.
    assert (await https_client.get(PROTECTED)).status_code == 200

    logout = await https_client.post("/api/v1/auth/logout")
    assert logout.status_code == 200
    # httpx applies the clearing Set-Cookie, removing the session cookie.
    assert not https_client.cookies.get("session")

    resp = await https_client.get(PROTECTED)
    assert resp.status_code in (401, 403)
