"""story-T2.3: CORS_ALLOW_ORIGINS is a configurable credentialed origin list.

Defaults include localhost + the *.lab.lsdmt.me lab origin(s); wildcard
subdomains are honoured via allow_origin_regex. allow_credentials stays True
(required for the httpOnly session cookie).
"""
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.core.config import Settings, settings


def test_cors_allow_origins_default_list():
    s = Settings()
    assert isinstance(s.CORS_ALLOW_ORIGINS, list)
    assert "http://localhost:3000" in s.CORS_ALLOW_ORIGINS
    # A lab origin must be reachable either as an explicit entry or via the regex.
    assert any("lab.lsdmt.me" in o for o in s.CORS_ALLOW_ORIGINS)


def test_existing_frontend_url_preserved():
    # T2.3 must APPEND, not rewrite: FRONTEND_URL stays with its old default.
    s = Settings()
    assert s.FRONTEND_URL == "http://localhost:3000"


@pytest_asyncio.fixture
async def app_client():
    from app.main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


async def test_allowed_lab_origin_echoed_with_credentials(app_client):
    origin = "https://hdt.lab.lsdmt.me"
    resp = await app_client.options(
        "/api/v1/health",
        headers={
            "Origin": origin,
            "Access-Control-Request-Method": "GET",
        },
    )
    assert resp.headers.get("access-control-allow-origin") == origin
    assert resp.headers.get("access-control-allow-credentials") == "true"


async def test_allowed_localhost_origin_echoed(app_client):
    origin = "http://localhost:3000"
    resp = await app_client.options(
        "/api/v1/health",
        headers={"Origin": origin, "Access-Control-Request-Method": "GET"},
    )
    assert resp.headers.get("access-control-allow-origin") == origin
    assert resp.headers.get("access-control-allow-credentials") == "true"


async def test_disallowed_origin_not_echoed(app_client):
    origin = "https://evil.example.com"
    resp = await app_client.options(
        "/api/v1/health",
        headers={"Origin": origin, "Access-Control-Request-Method": "GET"},
    )
    assert resp.headers.get("access-control-allow-origin") != origin
