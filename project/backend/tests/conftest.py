"""Shared pytest fixtures for the backend test suite.

Provides an isolated in-memory async SQLite database so tests never touch a real
Postgres/Redis instance, plus env defaults that keep the scheduler off and the
mock eBay client on. feature-002 extends this with an HTTP app client fixture.
"""
import os

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

# Force the mock eBay client during tests so no real network call is ever made.
# (The scheduler is kept off per-fixture where the app is constructed, not via a
# global env var, so config-default tests still see SCHEDULER_ENABLED's true default.)
os.environ.setdefault("USE_MOCK_EBAY", "true")

from app.models import Base  # noqa: E402  (import after env defaults; registers all tables)


@pytest_asyncio.fixture
async def engine():
    """A fresh in-memory SQLite engine with all tables created, per test."""
    eng = create_async_engine(
        "sqlite+aiosqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield eng
    await eng.dispose()


@pytest_asyncio.fixture
async def db(engine) -> AsyncSession:
    """An async session bound to the in-memory test database."""
    factory = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False, autoflush=False
    )
    async with factory() as session:
        yield session


@pytest_asyncio.fixture
async def client(db):
    """An authenticated HTTP client whose requests share the test `db` session.

    Overrides get_db (use the in-memory session) and get_current_user (a stub
    authenticated user) so endpoint tests need no real Postgres or JWT.
    """
    from app.api.deps import get_current_user, get_db
    from app.main import app
    from app.models.user import User

    async def _override_get_db():
        yield db

    async def _override_get_current_user():
        return User(id=1, username="tester", email="tester@example.com", hashed_password="x", is_active=True)

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_current_user] = _override_get_current_user
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as http_client:
        yield http_client
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def unauth_client(db):
    """An HTTP client that shares the test `db` session but does NOT stub auth.

    Only get_db is overridden, so requests exercise the real JWT auth path
    (register -> login -> bearer token -> protected route). Used by test_auth.
    """
    from app.api.deps import get_db
    from app.main import app

    async def _override_get_db():
        yield db

    app.dependency_overrides[get_db] = _override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as http_client:
        yield http_client
    app.dependency_overrides.clear()
