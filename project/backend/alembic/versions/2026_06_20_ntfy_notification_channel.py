"""Add ntfy notification channel columns

Adds ntfy_enabled / ntfy_topic / ntfy_min_score to notification_settings so deals
can also push to a self-hosted ntfy server (parallel to telegram/email).

Revision ID: ntfy_notification_channel
Revises: cascade_delete_tracked_items
"""
import sqlalchemy as sa
from alembic import op

revision = "ntfy_notification_channel"
down_revision = "cascade_delete_tracked_items"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "notification_settings",
        sa.Column("ntfy_enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )
    op.add_column(
        "notification_settings",
        sa.Column("ntfy_topic", sa.String(length=100), nullable=True),
    )
    op.add_column(
        "notification_settings",
        sa.Column("ntfy_min_score", sa.Integer(), nullable=False, server_default=sa.text("70")),
    )


def downgrade() -> None:
    op.drop_column("notification_settings", "ntfy_min_score")
    op.drop_column("notification_settings", "ntfy_topic")
    op.drop_column("notification_settings", "ntfy_enabled")
