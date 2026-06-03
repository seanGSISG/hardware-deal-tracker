"""Initial schema

Revision ID: init
Revises:
Create Date: 2026-01-13 00:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = 'init'
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table('users',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('username', sa.String(100), unique=True, nullable=False),
        sa.Column('email', sa.String(255), unique=True, nullable=False),
        sa.Column('hashed_password', sa.String(255), nullable=False),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('is_admin', sa.Boolean(), default=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table('tracked_items',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('keywords', sa.String(1000), nullable=False),
        sa.Column('sku', sa.String(100)),
        sa.Column('mpn', sa.String(100)),
        sa.Column('category_id', sa.String(20)),
        sa.Column('marketplace', sa.String(20), default='ebay'),
        sa.Column('target_price', sa.Numeric(10, 2)),
        sa.Column('alert_threshold', sa.Numeric(5, 2), default=0.20),
        sa.Column('min_deal_score', sa.Integer(), default=50),
        sa.Column('is_enabled', sa.Boolean(), default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('last_searched', sa.DateTime(timezone=True)),
        sa.Column('search_interval', sa.Integer(), default=600),
        sa.Column('scam_floor', sa.Numeric(10, 2)),
        sa.Column('benchmark_median', sa.Numeric(10, 2)),
        sa.Column('notes', sa.String(500)),
    )

    op.create_index('idx_tracked_items_enabled', 'tracked_items', ['is_enabled'])

    op.create_table('listings',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('marketplace_id', sa.String(50), unique=True, nullable=False),
        sa.Column('tracked_item_id', sa.Integer(), sa.ForeignKey('tracked_items.id')),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('normalized_title', sa.String(500)),
        sa.Column('price', sa.Numeric(10, 2), nullable=False),
        sa.Column('shipping', sa.Numeric(10, 2), default=0),
        sa.Column('seller', sa.String(200), nullable=False),
        sa.Column('seller_feedback', sa.Integer(), default=0),
        sa.Column('seller_positive_pct', sa.Numeric(5, 2), default=100.0),
        sa.Column('condition', sa.String(50)),
        sa.Column('condition_id', sa.String(20)),
        sa.Column('category_id', sa.String(20)),
        sa.Column('url', sa.String(2000), nullable=False),
        sa.Column('image_url', sa.String(2000)),
        sa.Column('is_auction', sa.Boolean(), default=False),
        sa.Column('quantity', sa.Integer(), default=1),
        sa.Column('buying_options', sa.JSON()),
        sa.Column('listing_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('end_date', sa.DateTime(timezone=True)),
        sa.Column('is_deduped', sa.Boolean(), default=False),
        sa.Column('raw_data', sa.JSON()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_index('idx_listings_marketplace_id', 'listings', ['marketplace_id'])
    op.create_index('idx_listings_tracked_item', 'listings', ['tracked_item_id'])

    op.create_table('price_history',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('listing_id', sa.Integer(), sa.ForeignKey('listings.id')),
        sa.Column('tracked_item_id', sa.Integer(), sa.ForeignKey('tracked_items.id')),
        sa.Column('observed_price', sa.Numeric(10, 2), nullable=False),
        sa.Column('shipping', sa.Numeric(10, 2), default=0),
        sa.Column('total_price', sa.Numeric(10, 2), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table('listing_scores',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('listing_id', sa.Integer(), sa.ForeignKey('listings.id')),
        sa.Column('tracked_item_id', sa.Integer(), sa.ForeignKey('tracked_items.id')),
        sa.Column('overall_score', sa.Integer(), nullable=False),
        sa.Column('deal_score', sa.Integer(), nullable=False),
        sa.Column('confidence', sa.Numeric(5, 2), nullable=False),
        sa.Column('classification', sa.String(50)),
        sa.Column('price_zscore', sa.Numeric(8, 4)),
        sa.Column('vs_median_pct', sa.Numeric(8, 4)),
        sa.Column('vs_lowest_pct', sa.Numeric(8, 4)),
        sa.Column('est_fair_value', sa.Numeric(10, 2)),
        sa.Column('scam_flag', sa.String(200)),
        sa.Column('scored_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_index('idx_scores_listing', 'listing_scores', ['listing_id'])
    op.create_index('idx_scores_overall', 'listing_scores', ['overall_score'])

    op.create_table('alerts',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('listing_id', sa.Integer(), sa.ForeignKey('listings.id')),
        sa.Column('tracked_item_id', sa.Integer(), sa.ForeignKey('tracked_items.id')),
        sa.Column('score_id', sa.Integer(), sa.ForeignKey('listing_scores.id')),
        sa.Column('channel', sa.String(20), nullable=False),
        sa.Column('alert_type', sa.String(20), nullable=False),
        sa.Column('was_sent', sa.Boolean(), default=False),
        sa.Column('sent_at', sa.DateTime(timezone=True)),
        sa.Column('template_used', sa.String(50)),
        sa.Column('telegram_msg_id', sa.String(100)),
        sa.Column('error_message', sa.String(1000)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table('notification_settings',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), unique=True),
        sa.Column('telegram_chat_id', sa.String(100)),
        sa.Column('telegram_enabled', sa.Boolean(), default=True),
        sa.Column('email_address', sa.String(255)),
        sa.Column('email_enabled', sa.Boolean(), default=True),
        sa.Column('email_digest_mode', sa.String(20), default='daily'),
        sa.Column('telegram_min_score', sa.Integer(), default=70),
        sa.Column('email_min_score', sa.Integer(), default=50),
        sa.Column('mute_until', sa.DateTime(timezone=True)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table('notification_settings')
    op.drop_table('alerts')
    op.drop_table('listing_scores')
    op.drop_table('price_history')
    op.drop_table('listings')
    op.drop_table('tracked_items')
    op.drop_table('users')
