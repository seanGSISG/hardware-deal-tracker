"""Unique constraint on tracked_items.name (T3.5 idempotent seed support).

The seed's INSERT ... ON CONFLICT (name) DO NOTHING needs a unique constraint on
`name` for the conflict target to be valid in Postgres. Also dedupes the catalog at
the DB level so the same SKU can't be tracked twice.

Revision ID: tracked_item_name_unique
Revises: server_defaults
Create Date: 2026-06-02 00:00:00.000000
"""
from collections.abc import Sequence

from alembic import op

revision: str = "tracked_item_name_unique"
down_revision: str | None = "server_defaults"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_unique_constraint("uq_tracked_items_name", "tracked_items", ["name"])


def downgrade() -> None:
    op.drop_constraint("uq_tracked_items_name", "tracked_items", type_="unique")
