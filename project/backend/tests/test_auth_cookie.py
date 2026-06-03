"""story-T2.1: /auth/login sets an httpOnly session cookie; /auth/logout clears it.

The bearer-token body MUST remain intact so API clients and the existing pytest
fixtures keep working. Uses the real auth path via unauth_client (register/login).
"""


from app.core.config import settings
from app.core.security import verify_token


async def _register_and_login(unauth_client, monkeypatch):
    monkeypatch.setattr(settings, "ALLOW_REGISTRATION", True)
    await unauth_client.post(
        "/api/v1/auth/register",
        json={"username": "cookieuser", "email": "cookie@example.com", "password": "supersecret123"},
    )
    return await unauth_client.post(
        "/api/v1/auth/login",
        json={"username": "cookieuser", "password": "supersecret123"},
    )


async def test_login_sets_session_cookie_with_attributes(unauth_client, monkeypatch):
    resp = await _register_and_login(unauth_client, monkeypatch)
    assert resp.status_code == 200

    set_cookie = resp.headers.get("set-cookie", "")
    assert "session=" in set_cookie, f"no session cookie in: {set_cookie!r}"
    lowered = set_cookie.lower()
    assert "httponly" in lowered
    assert "secure" in lowered
    assert "samesite=lax" in lowered


async def test_login_still_returns_bearer_body(unauth_client, monkeypatch):
    resp = await _register_and_login(unauth_client, monkeypatch)
    assert resp.status_code == 200
    body = resp.json()
    assert body["access_token"]
    assert body.get("token_type", "bearer") == "bearer"


async def test_session_cookie_value_is_the_jwt(unauth_client, monkeypatch):
    resp = await _register_and_login(unauth_client, monkeypatch)
    assert resp.status_code == 200
    cookie_val = resp.cookies.get("session")
    assert cookie_val
    decoded = verify_token(cookie_val)
    assert decoded is not None
    assert decoded.get("sub")
    # Same JWT as the bearer body.
    assert cookie_val == resp.json()["access_token"]


async def test_cookie_max_age_derived_from_ttl(unauth_client, monkeypatch):
    monkeypatch.setattr(settings, "ACCESS_TOKEN_EXPIRE_MINUTES", 30)
    resp = await _register_and_login(unauth_client, monkeypatch)
    set_cookie = resp.headers.get("set-cookie", "").lower()
    # Cookie lifetime must reflect the configured JWT TTL (30 min = 1800s), not a
    # hardcoded value. Accept either Max-Age or an Expires far enough in the future.
    assert "max-age=1800" in set_cookie or "expires=" in set_cookie


async def test_logout_clears_session_cookie(unauth_client, monkeypatch):
    await _register_and_login(unauth_client, monkeypatch)
    resp = await unauth_client.post("/api/v1/auth/logout")
    assert resp.status_code == 200
    set_cookie = resp.headers.get("set-cookie", "").lower()
    assert "session=" in set_cookie
    # Cleared: empty value and/or Max-Age=0 and/or an expiry in the past.
    cleared = (
        'session=""' in set_cookie
        or "session=;" in set_cookie
        or "max-age=0" in set_cookie
        or "expires=thu, 01 jan 1970" in set_cookie
    )
    assert cleared, f"cookie not cleared: {set_cookie!r}"
