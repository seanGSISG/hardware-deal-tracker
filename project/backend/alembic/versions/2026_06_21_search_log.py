"""Add search_log activity-audit table

Persists one row per per-item search (ok/skipped/error) so the dashboard
Activity page has a durable backing store. tracked_item_id is SET NULL on item
delete and item_name is denormalised so history survives item removal.

Revision ID: search_log
Revises: ntfy_notification_channel
"""
import sqlalchemy as sa
from alembic import op

revision = "search_log"
down_revision = "ntfy_notification_channel"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "search_log",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tracked_item_id", sa.Integer(), nullable=True),
        sa.Column("item_name", sa.String(length=300), nullable=False),
        sa.Column("source", sa.String(length=50), nullable=False, server_default="ebay"),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("priority", sa.String(length=10), nullable=True),
        sa.Column("listings_found", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("new_listings", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("duplicates", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("calls_used", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("duration_ms", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("detail", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["tracked_item_id"], ["tracked_items.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_search_log_tracked_item_id", "search_log", ["tracked_item_id"])
    op.create_index("ix_search_log_status", "search_log", ["status"])
    op.create_index("ix_search_log_created_at", "search_log", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_search_log_created_at", table_name="search_log")
    op.drop_index("ix_search_log_status", table_name="search_log")
    op.drop_index("ix_search_log_tracked_item_id", table_name="search_log")
    op.drop_table("search_log")
