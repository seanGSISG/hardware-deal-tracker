"""AI deal analysis: ai_analyses table (feature-006)

Stores per-listing LLM verdicts: deal grade + reasoning, scam signal + reasons,
and extracted structured specs, with provider/model provenance.

Revision ID: ai_analyses
Revises: sources
Create Date: 2026-06-02 00:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "ai_analyses"
down_revision: str | None = "sources"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "ai_analyses",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("listing_id", sa.Integer(), sa.ForeignKey("listings.id"), nullable=False),
        sa.Column("tracked_item_id", sa.Integer(), sa.ForeignKey("tracked_items.id"), nullable=True),
        sa.Column("provider", sa.String(length=30), nullable=False),
        sa.Column("model", sa.String(length=120), nullable=False),
        sa.Column("deal_grade", sa.String(length=40), nullable=True),
        sa.Column("reasoning", sa.Text(), nullable=True),
        sa.Column("scam_signal", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("scam_reasons", sa.JSON(), nullable=True),
        sa.Column("extracted_specs", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_ai_analyses_listing_id", "ai_analyses", ["listing_id"])


def downgrade() -> None:
    op.drop_index("ix_ai_analyses_listing_id", table_name="ai_analyses")
    op.drop_table("ai_analyses")
