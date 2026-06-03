"""Optional semantic-matching embeddings: pgvector extension + embedding column

STRETCH / OPTIONAL (feature-006, ADR-006). Creates the pgvector extension and
adds a nullable ``embedding`` vector column to ``tracked_items`` for semantic
catalog matching. The whole feature is gated behind ENABLE_SEMANTIC_MATCHING at
runtime; this migration only prepares the schema.

DIALECT GUARD: the in-memory sqlite test DB cannot load pgvector, so on any
non-Postgres dialect this migration emits a JSON column instead of a real
``vector(N)`` column and skips the CREATE EXTENSION. On Postgres the column is a
genuine ``vector(SEMANTIC_EMBEDDING_DIM)``. Dimension comes from config, not a
scattered literal.

Revision ID: semantic_embeddings
Revises: item_price_baselines
Create Date: 2026-06-02 00:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op
from app.core.config import settings

revision: str = "semantic_embeddings"
down_revision: str | None = "item_price_baselines"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _embedding_column_type():
    """pgvector vector(N) on Postgres, JSON elsewhere (sqlite cannot load pgvector)."""
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        from pgvector.sqlalchemy import Vector

        return Vector(settings.SEMANTIC_EMBEDDING_DIM)
    return sa.JSON()


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.add_column(
        "tracked_items",
        sa.Column("embedding", _embedding_column_type(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("tracked_items", "embedding")
    # Extension drop is intentionally NOT performed: other objects may depend on
    # it and CREATE EXTENSION IF NOT EXISTS is idempotent on re-upgrade.
