"""Rolling per-item sold-comps baseline: item_price_baselines table (feature-001)

Persists one current rolling baseline snapshot per tracked item (Tukey-trimmed
median/IQR/stats + 30d trend), refreshed daily by ScoringBaselineService. Fills
the EbayPoller._historical_stats_for() scoring seam (ADR-001).

Revision ID: item_price_baselines
Revises: ai_analyses
Create Date: 2026-06-02 00:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "item_price_baselines"
down_revision: str | None = "ai_analyses"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "item_price_baselines",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "tracked_item_id",
            sa.Integer(),
            sa.ForeignKey("tracked_items.id"),
            nullable=False,
            unique=True,
        ),
        sa.Column("median_price", sa.Numeric(10, 2), nullable=True),
        sa.Column("avg_price", sa.Numeric(10, 2), nullable=True),
        sa.Column("std_dev", sa.Numeric(10, 2), nullable=True),
        sa.Column("min_price", sa.Numeric(10, 2), nullable=True),
        sa.Column("q1", sa.Numeric(10, 2), nullable=True),
        sa.Column("q3", sa.Numeric(10, 2), nullable=True),
        sa.Column("data_points", sa.Integer(), server_default="0", nullable=False),
        sa.Column("lookback_days", sa.Integer(), nullable=True),
        sa.Column("trend_direction", sa.String(length=20), nullable=True),
        sa.Column("trend_slope_pct", sa.Numeric(8, 4), nullable=True),
        sa.Column("source", sa.String(length=20), nullable=False, server_default="benchmark"),
        sa.Column(
            "computed_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_item_price_baselines_tracked_item_id",
        "item_price_baselines",
        ["tracked_item_id"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_item_price_baselines_tracked_item_id", table_name="item_price_baselines"
    )
    op.drop_table("item_price_baselines")
