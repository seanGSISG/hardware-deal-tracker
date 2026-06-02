"""Shared pytest fixtures for the backend test suite.

Provides an isolated in-memory async SQLite database so tests never touch a real
Postgres/Redis instance, plus env defaults that keep the scheduler off and the
mock eBay client on. feature-002 extends this with an HTTP app client fixture.
"""
import os

import pytest_asyncio
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
