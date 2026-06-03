"""Add server_default to tracked_items and users columns (T3.3 audit).

Columns previously relied on ORM-side `default=` only, so rows inserted via raw
SQL (seed scripts, psql, other services) got NULL. This locks the defaults at the
database level for marketplace/alert_threshold/min_deal_score/is_enabled/
search_interval (tracked_items) and is_active/is_admin (users).

Revision ID: server_defaults
Revises: init
Create Date: 2026-06-02 00:00:00.000000
"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "server_defaults"
down_revision: str | None = "init"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.alter_column("tracked_items", "marketplace", server_default="ebay")
    op.alter_column("tracked_items", "alert_threshold", server_default=sa.text("0.20"))
    op.alter_column("tracked_items", "min_deal_score", server_default=sa.text("50"))
    op.alter_column("tracked_items", "is_enabled", server_default=sa.text("true"))
    op.alter_column("tracked_items", "search_interval", server_default=sa.text("600"))
    op.alter_column("users", "is_active", server_default=sa.text("true"))
    op.alter_column("users", "is_admin", server_default=sa.text("false"))


def downgrade() -> None:
    op.alter_column("tracked_items", "marketplace", server_default=None)
    op.alter_column("tracked_items", "alert_threshold", server_default=None)
    op.alter_column("tracked_items", "min_deal_score", server_default=None)
    op.alter_column("tracked_items", "is_enabled", server_default=None)
    op.alter_column("tracked_items", "search_interval", server_default=None)
    op.alter_column("users", "is_active", server_default=None)
    op.alter_column("users", "is_admin", server_default=None)
