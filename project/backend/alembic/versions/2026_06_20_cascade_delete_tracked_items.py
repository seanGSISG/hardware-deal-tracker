"""ON DELETE CASCADE for all FKs referencing tracked_items

Deleting a tracked item failed with a FK violation because the 7 child tables
(listings, price_history, listing_scores, alerts, ai_analyses,
item_price_baselines, community_signal_leads) referenced tracked_items with the
default NO ACTION. Recreate each FK with ON DELETE CASCADE so removing a tracked
item cleans up its dependent rows.

Revision ID: cascade_delete_tracked_items
Revises: community_signal_leads
"""
from alembic import op

revision = "cascade_delete_tracked_items"
down_revision = "community_signal_leads"
branch_labels = None
depends_on = None

# (table, constraint_name, column)
_FKS = [
    ("listings", "listings_tracked_item_id_fkey", "tracked_item_id"),
    ("price_history", "price_history_tracked_item_id_fkey", "tracked_item_id"),
    ("listing_scores", "listing_scores_tracked_item_id_fkey", "tracked_item_id"),
    ("alerts", "alerts_tracked_item_id_fkey", "tracked_item_id"),
    ("ai_analyses", "ai_analyses_tracked_item_id_fkey", "tracked_item_id"),
    ("item_price_baselines", "item_price_baselines_tracked_item_id_fkey", "tracked_item_id"),
    ("community_signal_leads", "community_signal_leads_catalog_item_id_fkey", "catalog_item_id"),
]


def upgrade() -> None:
    bind = op.get_bind()
    # SQLite (test DB) builds FKs from model metadata via create_all and can't
    # ALTER constraints; the ondelete on the model columns already covers it.
    if bind.dialect.name == "sqlite":
        return
    for table, name, col in _FKS:
        op.execute(f'ALTER TABLE {table} DROP CONSTRAINT IF EXISTS {name}')
        op.execute(
            f'ALTER TABLE {table} ADD CONSTRAINT {name} '
            f'FOREIGN KEY ({col}) REFERENCES tracked_items(id) ON DELETE CASCADE'
        )


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "sqlite":
        return
    for table, name, col in _FKS:
        op.execute(f'ALTER TABLE {table} DROP CONSTRAINT IF EXISTS {name}')
        op.execute(
            f'ALTER TABLE {table} ADD CONSTRAINT {name} '
            f'FOREIGN KEY ({col}) REFERENCES tracked_items(id)'
        )
