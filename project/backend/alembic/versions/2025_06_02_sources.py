"""Multi-source ingestion: listings.source + tracked_items.pcpp_product_id

Adds source-awareness for the SourceAdapter abstraction (feature-005):
- listings.source + composite unique (source, marketplace_id) replacing the
  single-column unique on marketplace_id.
- tracked_items.pcpp_product_id to map mappable items to a PCPartPicker product
  for benchmark refresh.

Revision ID: sources
Revises: init
Create Date: 2026-06-02 00:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "sources"
down_revision: str | None = "init"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # listings.source
    op.add_column(
        "listings",
        sa.Column("source", sa.String(30), nullable=False, server_default="ebay"),
    )
    # widen marketplace_id (Shopify variant ids / other sources can be longer)
    op.alter_column("listings", "marketplace_id", type_=sa.String(100), existing_type=sa.String(50))

    # Replace single-column unique on marketplace_id with composite (source, marketplace_id).
    # The original unique was created implicitly via the column's unique=True; drop it by name
    # where present, then add the composite constraint.
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("ALTER TABLE listings DROP CONSTRAINT IF EXISTS listings_marketplace_id_key")
    op.create_unique_constraint(
        "uq_listings_source_marketplace_id", "listings", ["source", "marketplace_id"]
    )

    # tracked_items.pcpp_product_id (PCPartPicker benchmark mapping; nullable).
    op.add_column("tracked_items", sa.Column("pcpp_product_id", sa.String(100), nullable=True))


def downgrade() -> None:
    op.drop_column("tracked_items", "pcpp_product_id")
    op.drop_constraint("uq_listings_source_marketplace_id", "listings", type_="unique")
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.create_unique_constraint("listings_marketplace_id_key", "listings", ["marketplace_id"])
    op.alter_column("listings", "marketplace_id", type_=sa.String(50), existing_type=sa.String(100))
    op.drop_column("listings", "source")
