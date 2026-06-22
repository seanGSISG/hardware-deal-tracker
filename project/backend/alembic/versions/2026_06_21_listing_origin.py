"""Add listing origin columns (item_country, is_china)

Stamps each listing with its eBay itemLocation.country (ISO-3166 alpha-2) and a
derived China-origin flag so the dashboard can badge China-shipped listings.
Both are additive and backfill-free: existing rows keep NULL country / False flag
until re-polled.

Revision ID: listing_origin
Revises: search_log
"""
import sqlalchemy as sa
from alembic import op

revision = "listing_origin"
down_revision = "search_log"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("listings", sa.Column("item_country", sa.String(length=2), nullable=True))
    op.add_column(
        "listings",
        sa.Column("is_china", sa.Boolean(), nullable=False, server_default="false"),
    )


def downgrade() -> None:
    op.drop_column("listings", "is_china")
    op.drop_column("listings", "item_country")
