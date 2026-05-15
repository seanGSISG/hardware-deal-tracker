# Database Guide

> PostgreSQL schema, migrations, and query patterns. Read this when changing models or writing raw SQL.

---

## Schema Overview

7 tables, all using SQLAlchemy 2.0 `mapped_column` syntax with asyncpg.

```
users                      # Single admin user (seeded)
tracked_items              # 34 hardware items being monitored
listings                   # Individual eBay search results
listing_scores             # Deal scores per listing
price_history              # Price snapshots over time
alerts                     # Triggered deal alerts
notification_settings      # Telegram/SMTP config per user
```

---

## Table Reference

### `users`

| Column | Type | Notes |
|--------|------|-------|
| `id` | SERIAL PK | |
| `username` | VARCHAR(50) UNIQUE | Default: `admin` |
| `email` | VARCHAR(255) | |
| `hashed_password` | VARCHAR(255) | bcrypt hash |
| `is_active` | BOOLEAN | Default: `true` |
| `created_at` | TIMESTAMP | Auto |

### `tracked_items` (core table)

| Column | Type | Notes |
|--------|------|-------|
| `id` | SERIAL PK | |
| `name` | VARCHAR(255) | Display name, e.g. "AMD EPYC 7F72" |
| `search_keywords` | VARCHAR(500) | eBay search query string |
| `ebay_category_id` | VARCHAR(50) | eBay category filter (optional) |
| `target_price` | DECIMAL(12,2) | Alert threshold in USD |
| `search_interval` | INTEGER | Seconds between polls (default: 300) |
| `is_active` | BOOLEAN | Enable/disable (default: `true`) |
| `scam_floor` | DECIMAL(12,2) | Below this = suspicious listing |
| `benchmark_median` | DECIMAL(12,2) | Research-validated median price |
| `notes` | TEXT | Human-readable context |
| `created_at` | TIMESTAMP | Auto |
| `updated_at` | TIMESTAMP | Auto |

**The `search_interval` drives the priority tier:**
- `≤300` (5 min) → P0 Hot
- `301-600` (10 min) → P1 Standard
- `601-1200` (20 min) → P2 Monitor
- `>1200` (30+ min) → P3 Passive

### `listings`

| Column | Type | Notes |
|--------|------|-------|
| `id` | SERIAL PK | |
| `tracked_item_id` | FK → tracked_items | |
| `ebay_item_id` | VARCHAR(50) UNIQUE | eBay's item ID |
| `title` | VARCHAR(500) | Listing title |
| `price` | DECIMAL(12,2) | Current price |
| `shipping` | DECIMAL(12,2) | Shipping cost |
| `total_price` | DECIMAL(12,2) | price + shipping |
| `currency` | VARCHAR(3) | Default: USD |
| `condition` | VARCHAR(50) | New, Used, Open Box, etc. |
| `seller_name` | VARCHAR(100) | |
| `seller_rating` | DECIMAL(3,2) | 0.00 - 5.00 |
| `seller_feedback_count` | INTEGER | |
| `seller_top_rated` | BOOLEAN | |
| `listing_url` | VARCHAR(1000) | Direct eBay URL |
| `image_url` | VARCHAR(1000) | Primary image |
| `quantity` | INTEGER | Available quantity |
| `is_buy_it_now` | BOOLEAN | |
| `is_auction` | BOOLEAN | |
| `ends_at` | TIMESTAMP | Auction end time |
| `is_active` | BOOLEAN | Still available? |
| `created_at` | TIMESTAMP | First seen |
| `updated_at` | TIMESTAMP | Last refresh |

### `listing_scores`

| Column | Type | Notes |
|--------|------|-------|
| `id` | SERIAL PK | |
| `listing_id` | FK → listings UNIQUE | One score per listing |
| `total_score` | DECIMAL(5,2) | 0.00 - 100.00 |
| `z_score_component` | DECIMAL(5,2) | Price Z-score (30%) |
| `discount_component` | DECIMAL(5,2) | Discount ratio (25%) |
| `seller_component` | DECIMAL(5,2) | Seller quality (15%) |
| `quality_component` | DECIMAL(5,2) | Item condition (15%) |
| `timing_component` | DECIMAL(5,2) | Urgency (10%) |
| `bulk_component` | DECIMAL(5,2) | Quantity bonus (5%) |
| `is_scam_flagged` | BOOLEAN | Below scam_floor? |
| `scam_floor_hit` | DECIMAL(12,2) | Which floor was hit |
| `scoring_version` | VARCHAR(10) | Algorithm version |
| `created_at` | TIMESTAMP | |

### `price_history`

| Column | Type | Notes |
|--------|------|-------|
| `id` | BIGSERIAL PK | |
| `tracked_item_id` | FK → tracked_items | |
| `avg_price` | DECIMAL(12,2) | Mean price this poll |
| `min_price` | DECIMAL(12,2) | Lowest price |
| `max_price` | DECIMAL(12,2) | Highest price |
| `listing_count` | INTEGER | How many listings |
| `scored_at` | TIMESTAMP | When snapshot taken |

### `alerts`

| Column | Type | Notes |
|--------|------|-------|
| `id` | SERIAL PK | |
| `tracked_item_id` | FK → tracked_items | |
| `listing_id` | FK → listings | |
| `score_id` | FK → listing_scores | |
| `alert_type` | VARCHAR(20) | `deal`, `price_drop`, `scam` |
| `message` | TEXT | Human-readable alert |
| `is_dismissed` | BOOLEAN | Default: false |
| `sent_telegram` | BOOLEAN | |
| `sent_email` | BOOLEAN | |
| `created_at` | TIMESTAMP | |

### `notification_settings`

| Column | Type | Notes |
|--------|------|-------|
| `id` | SERIAL PK | |
| `user_id` | FK → users | |
| `telegram_enabled` | BOOLEAN | |
| `telegram_bot_token` | VARCHAR(255) | |
| `telegram_chat_id` | VARCHAR(100) | |
| `email_enabled` | BOOLEAN | |
| `smtp_host` | VARCHAR(255) | |
| `smtp_port` | INTEGER | Default: 587 |
| `smtp_user` | VARCHAR(255) | |
| `smtp_password` | VARCHAR(255) | |
| `min_score_threshold` | DECIMAL(5,2) | Only alert above this score |
| `created_at` | TIMESTAMP | |
| `updated_at` | TIMESTAMP | |

---

## Migrations

Uses Alembic with asyncpg driver.

### Configuration

- Config file: `backend/alembic/alembic.ini`
- Environment script: `backend/alembic/env.py`
- Migration versions: `backend/alembic/versions/`

### Common Commands

```bash
# Run migrations (inside container)
make migrate
# Or: docker compose exec backend alembic upgrade head

# Create new migration (inside container)
docker compose exec backend alembic revision --autogenerate -m "description"

# Downgrade one step
docker compose exec backend alembic downgrade -1

# View current version
docker compose exec backend alembic current
```

### Creating a New Migration

1. Edit SQLAlchemy model(s) in `app/models/`
2. Run autogenerate (see above)
3. **Review the generated migration file** — autogenerate can miss things
4. Run `make migrate` to apply

### Manual Migration (if autogenerate fails)

```python
# alembic/versions/2025_01_14_add_column.py
from alembic import op
import sqlalchemy as sa

revision = "..."
down_revision = "..."

def upgrade():
    op.add_column("tracked_items", sa.Column("new_field", sa.String(100), nullable=True))

def downgrade():
    op.drop_column("tracked_items", "new_field")
```

---

## Query Patterns

### Async SELECT

```python
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.tracked_item import TrackedItem

async def get_active_items(db: AsyncSession):
    result = await db.execute(
        select(TrackedItem).where(TrackedItem.is_active == True)
    )
    return result.scalars().all()
```

### Async INSERT

```python
async def create_item(db: AsyncSession, name: str, ...):
    item = TrackedItem(name=name, ...)
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return item
```

### Async UPDATE

```python
async def update_interval(db: AsyncSession, item_id: int, interval: int):
    result = await db.execute(
        select(TrackedItem).where(TrackedItem.id == item_id)
    )
    item = result.scalar_one()
    item.search_interval = interval
    await db.commit()
    return item
```

### Async DELETE

```python
async def delete_item(db: AsyncSession, item_id: int):
    result = await db.execute(
        select(TrackedItem).where(TrackedItem.id == item_id)
    )
    item = result.scalar_one()
    await db.delete(item)
    await db.commit()
```

### Join Query (Listings with Scores)

```python
from sqlalchemy.orm import joinedload

result = await db.execute(
    select(Listing)
    .options(joinedload(Listing.score))
    .where(Listing.tracked_item_id == item_id)
    .order_by(Listing.created_at.desc())
)
listings = result.scalars().all()
# Access score via: listing.score.total_score
```

---

## Indexes

Recommended indexes for common queries (add via migration if not present):

```sql
-- Poller queries
CREATE INDEX idx_tracked_items_active ON tracked_items(is_active);
CREATE INDEX idx_tracked_items_interval ON tracked_items(search_interval);

-- Listing lookups
CREATE INDEX idx_listings_item_id ON listings(tracked_item_id);
CREATE INDEX idx_listings_ebay_id ON listings(ebay_item_id);
CREATE INDEX idx_listings_created ON listings(created_at DESC);

-- Score lookups
CREATE INDEX idx_scores_listing_id ON listing_scores(listing_id);
CREATE INDEX idx_scores_total ON listing_scores(total_score DESC);

-- Price history time series
CREATE INDEX idx_price_history_item ON price_history(tracked_item_id);
CREATE INDEX idx_price_history_scored ON price_history(scored_at DESC);

-- Alert queries
CREATE INDEX idx_alerts_dismissed ON alerts(is_dismissed) WHERE is_dismissed = false;
```

---

## Seed Data

`backend/scripts/seed_data_v2.sql` contains:
- 1 admin user (`admin` / `admin123`)
- 34 tracked items with research-validated pricing

Apply with: `make seed`

The seed data inserts directly into `tracked_items` with all fields including `scam_floor` and `benchmark_median`. When adding new items, update both the SQL file AND `services/ebay/catalog.py`.
