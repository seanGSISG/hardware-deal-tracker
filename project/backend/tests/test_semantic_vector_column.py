"""story-1 (feature-006): dialect-guarded vector embedding column.

The semantic-matching feature stores an optional embedding vector on tracked
items. On Postgres this materialises as a real pgvector column; on the
in-memory sqlite test DB pgvector cannot load, so the column must degrade to a
JSON-storable type that Base.metadata.create_all can build. These tests run on
sqlite and prove the schema is buildable and the column round-trips a vector.
"""
import pytest_asyncio
from sqlalchemy import inspect, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.core.config import settings
from app.db.vector_type import EmbeddingVector
from app.models import Base
from app.models.tracked_item import TrackedItem


@pytest_asyncio.fixture
async def sqlite_engine():
    eng = create_async_engine(
        "sqlite+aiosqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield eng
    await eng.dispose()


def test_embedding_column_registered_on_model():
    """The model metadata carries the embedding column without importing pgvector."""
    cols = {c.name for c in TrackedItem.__table__.columns}
    assert "embedding" in cols
    col = TrackedItem.__table__.c.embedding
    assert isinstance(col.type, EmbeddingVector)
    assert col.nullable is True


def test_embedding_dim_sourced_from_config():
    """Column dimension comes from config, not a scattered literal."""
    assert TrackedItem.__table__.c.embedding.type.dim == settings.SEMANTIC_EMBEDDING_DIM


async def test_schema_creates_on_sqlite(sqlite_engine):
    """create_all must succeed on sqlite (vector column does not require pgvector)."""
    async with sqlite_engine.begin() as conn:
        names = await conn.run_sync(
            lambda sync_conn: inspect(sync_conn).get_table_names()
        )
    assert "tracked_items" in names


async def test_embedding_roundtrips_on_sqlite(sqlite_engine):
    """A list-of-floats embedding can be stored and read back on sqlite."""
    factory = async_sessionmaker(sqlite_engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        item = TrackedItem(
            name="EPYC 7003 test",
            keywords="epyc 7003",
            embedding=[0.1, 0.2, 0.3],
        )
        session.add(item)
        await session.commit()
        loaded = (await session.execute(select(TrackedItem))).scalar_one()
        assert list(loaded.embedding) == [0.1, 0.2, 0.3]


async def test_embedding_nullable_default(sqlite_engine):
    """An item with no embedding stores NULL cleanly."""
    factory = async_sessionmaker(sqlite_engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        item = TrackedItem(name="No embed", keywords="kw")
        session.add(item)
        await session.commit()
        loaded = (await session.execute(select(TrackedItem))).scalar_one()
        assert loaded.embedding is None
