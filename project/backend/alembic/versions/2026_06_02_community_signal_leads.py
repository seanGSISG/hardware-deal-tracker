"""Community-signal leads: community_signal_leads table (feature-007, ADR-007)

A SEPARATE leads surface for AI-extracted peer-to-peer deal posts (Reddit
r/homelabsales, STH). NOT routed through scoring/notifications. Dedup is enforced
by a unique (source, source_post_id) constraint.

Revision ID: community_signal_leads
Revises: item_price_baselines
Create Date: 2026-06-02 00:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "community_signal_leads"
down_revision: str | None = "semantic_embeddings"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "community_signal_leads",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("source", sa.String(length=40), nullable=False),
        sa.Column("source_post_id", sa.String(length=100), nullable=False),
        sa.Column(
            "catalog_item_id",
            sa.Integer(),
            sa.ForeignKey("tracked_items.id"),
            nullable=True,
        ),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("url", sa.String(length=2000), nullable=False),
        sa.Column("author", sa.String(length=200), nullable=True),
        sa.Column("model", sa.String(length=255), nullable=True),
        sa.Column("price", sa.Numeric(10, 2), nullable=True),
        sa.Column("condition", sa.String(length=80), nullable=True),
        sa.Column("location", sa.String(length=120), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="unknown"),
        sa.Column("confidence", sa.Numeric(4, 3), nullable=True),
        sa.Column("ai_reason", sa.String(length=500), nullable=True),
        sa.Column("raw_payload", sa.JSON(), nullable=True),
        sa.Column("posted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "ingested_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint(
            "source", "source_post_id", name="uq_community_signal_leads_source_post"
        ),
    )
    op.create_index(
        "ix_community_signal_leads_catalog_item_id",
        "community_signal_leads",
        ["catalog_item_id"],
    )
    op.create_index(
        "ix_community_signal_leads_ingested_at",
        "community_signal_leads",
        ["ingested_at"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_community_signal_leads_ingested_at", table_name="community_signal_leads"
    )
    op.drop_index(
        "ix_community_signal_leads_catalog_item_id", table_name="community_signal_leads"
    )
    op.drop_table("community_signal_leads")
