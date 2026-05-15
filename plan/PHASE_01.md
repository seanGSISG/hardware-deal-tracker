# PHASE 01 — Database Schema & Migrations

## Objective
Define and implement the complete PostgreSQL database schema with SQLAlchemy 2.0 models, Alembic migrations, and seed data.

---

## Output Location
All files in `/mnt/agents/output/hardware-deal-tracker/project/backend/`

---

## Dependencies
- Phase 0 scaffold must be in `main` branch
- The phase-01-database branch should be created from main

---

## Tasks

### Task 1: Database Configuration (`backend/app/db/base.py`)

Create the SQLAlchemy 2.0 DeclarativeBase with proper async patterns:

```python
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.ext.asyncio import AsyncAttrs

class Base(AsyncAttrs, DeclarativeBase):
    """Base class for all models."""
    pass
```

### Task 2: SQLAlchemy Models (8 models)

Create each model in `backend/app/models/` following SQLAlchemy 2.0 Mapped syntax:

**`backend/app/models/user.py`**
```python
from datetime import datetime
from sqlalchemy import String, Boolean, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
```

**`backend/app/models/tracked_item.py`**
```python
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Numeric, Boolean, DateTime, Integer, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

class TrackedItem(Base):
    __tablename__ = "tracked_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    keywords: Mapped[str] = mapped_column(String(1000), nullable=False)
    sku: Mapped[Optional[str]] = mapped_column(String(100))
    mpn: Mapped[Optional[str]] = mapped_column(String(100))
    category_id: Mapped[Optional[str]] = mapped_column(String(20))
    marketplace: Mapped[str] = mapped_column(String(20), default="ebay")
    target_price: Mapped[Optional[float]] = mapped_column(Numeric(10, 2))
    alert_threshold: Mapped[float] = mapped_column(Numeric(5, 2), default=0.20)
    min_deal_score: Mapped[int] = mapped_column(Integer, default=50)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    last_searched: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    search_interval: Mapped[int] = mapped_column(Integer, default=300)
    scam_floor: Mapped[Optional[float]] = mapped_column(Numeric(10, 2))
    benchmark_median: Mapped[Optional[float]] = mapped_column(Numeric(10, 2))
    notes: Mapped[Optional[str]] = mapped_column(String(500))

    # Relationships (Phase 2 will need these)
    listings: Mapped[list["Listing"]] = relationship("Listing", back_populates="tracked_item")
    price_history: Mapped[list["PriceHistory"]] = relationship("PriceHistory", back_populates="tracked_item")

    def get_priority_tier(self) -> str:
        """Map interval to priority tier for UI display."""
        if self.search_interval <= 360:
            return "P0"  # Hot
        elif self.search_interval <= 600:
            return "P1"  # Standard
        elif self.search_interval <= 1200:
            return "P2"  # Monitor
        return "P3"  # Passive
```

**`backend/app/models/listing.py`**
```python
from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, Numeric, Boolean, DateTime, Integer, JSON, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

class Listing(Base):
    __tablename__ = "listings"

    id: Mapped[int] = mapped_column(primary_key=True)
    marketplace_id: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    tracked_item_id: Mapped[Optional[int]] = mapped_column(ForeignKey("tracked_items.id"))
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    normalized_title: Mapped[Optional[str]] = mapped_column(String(500))
    price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    shipping: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    seller: Mapped[str] = mapped_column(String(200), nullable=False)
    seller_feedback: Mapped[int] = mapped_column(Integer, default=0)
    seller_positive_pct: Mapped[float] = mapped_column(Numeric(5, 2), default=100.0)
    condition: Mapped[Optional[str]] = mapped_column(String(50))
    condition_id: Mapped[Optional[str]] = mapped_column(String(20))
    category_id: Mapped[Optional[str]] = mapped_column(String(20))
    url: Mapped[str] = mapped_column(String(2000), nullable=False)
    image_url: Mapped[Optional[str]] = mapped_column(String(2000))
    is_auction: Mapped[bool] = mapped_column(Boolean, default=False)
    quantity: Mapped[int] = mapped_column(Integer, default=1)
    buying_options: Mapped[Optional[List[str]]] = mapped_column(JSON)
    listing_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    is_deduped: Mapped[bool] = mapped_column(Boolean, default=False)
    raw_data: Mapped[Optional[dict]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    tracked_item: Mapped[Optional["TrackedItem"]] = relationship("TrackedItem", back_populates="listings")
    scores: Mapped[list["ListingScore"]] = relationship("ListingScore", back_populates="listing")
    alerts: Mapped[list["Alert"]] = relationship("Alert", back_populates="listing")
```

**`backend/app/models/price_history.py`**
```python
from datetime import datetime
from sqlalchemy import Numeric, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

class PriceHistory(Base):
    __tablename__ = "price_history"

    id: Mapped[int] = mapped_column(primary_key=True)
    listing_id: Mapped[int] = mapped_column(ForeignKey("listings.id"))
    tracked_item_id: Mapped[int] = mapped_column(ForeignKey("tracked_items.id"))
    observed_price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    shipping: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    total_price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    tracked_item: Mapped["TrackedItem"] = relationship("TrackedItem", back_populates="price_history")
```

**`backend/app/models/listing_score.py`**
```python
from datetime import datetime
from sqlalchemy import String, Numeric, Integer, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

class ListingScore(Base):
    __tablename__ = "listing_scores"

    id: Mapped[int] = mapped_column(primary_key=True)
    listing_id: Mapped[int] = mapped_column(ForeignKey("listings.id"))
    tracked_item_id: Mapped[int] = mapped_column(ForeignKey("tracked_items.id"))
    overall_score: Mapped[int] = mapped_column(Integer, nullable=False)
    deal_score: Mapped[int] = mapped_column(Integer, nullable=False)
    confidence: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    classification: Mapped[str] = mapped_column(String(50))
    price_zscore: Mapped[Optional[float]] = mapped_column(Numeric(8, 4))
    vs_median_pct: Mapped[Optional[float]] = mapped_column(Numeric(8, 4))
    vs_lowest_pct: Mapped[Optional[float]] = mapped_column(Numeric(8, 4))
    est_fair_value: Mapped[Optional[float]] = mapped_column(Numeric(10, 2))
    scored_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    listing: Mapped["Listing"] = relationship("Listing", back_populates="scores")
```

**`backend/app/models/alert.py`**
```python
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Boolean, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(primary_key=True)
    listing_id: Mapped[int] = mapped_column(ForeignKey("listings.id"))
    tracked_item_id: Mapped[int] = mapped_column(ForeignKey("tracked_items.id"))
    score_id: Mapped[Optional[int]] = mapped_column(ForeignKey("listing_scores.id"))
    channel: Mapped[str] = mapped_column(String(20), nullable=False)
    alert_type: Mapped[str] = mapped_column(String(20), nullable=False)
    was_sent: Mapped[bool] = mapped_column(Boolean, default=False)
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    template_used: Mapped[Optional[str]] = mapped_column(String(50))
    telegram_msg_id: Mapped[Optional[str]] = mapped_column(String(100))
    error_message: Mapped[Optional[str]] = mapped_column(String(1000))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    listing: Mapped["Listing"] = relationship("Listing", back_populates="alerts")
```

**`backend/app/models/notification_setting.py`**
```python
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Boolean, DateTime, Integer, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

class NotificationSetting(Base):
    __tablename__ = "notification_settings"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)
    telegram_chat_id: Mapped[Optional[str]] = mapped_column(String(100))
    telegram_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    email_address: Mapped[Optional[str]] = mapped_column(String(255))
    email_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    email_digest_mode: Mapped[str] = mapped_column(String(20), default="daily")
    telegram_min_score: Mapped[int] = mapped_column(Integer, default=70)
    email_min_score: Mapped[int] = mapped_column(Integer, default=50)
    mute_until: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="notification_settings")
```

**`backend/app/models/__init__.py`** — Export all models in correct import order:
```python
from app.db.base import Base
from app.models.user import User
from app.models.tracked_item import TrackedItem
from app.models.listing import Listing
from app.models.price_history import PriceHistory
from app.models.listing_score import ListingScore
from app.models.alert import Alert
from app.models.notification_setting import NotificationSetting

__all__ = [
    "Base",
    "User",
    "TrackedItem",
    "Listing",
    "PriceHistory",
    "ListingScore",
    "Alert",
    "NotificationSetting",
]
```

### Task 3: Update Alembic env.py

Update `backend/alembic/env.py` to:
1. Import `Base` from `app.models`
2. Set `target_metadata = Base.metadata`
3. Read `DATABASE_URL` from environment variable

### Task 4: Create Initial Migration

Generate the initial migration:
```bash
cd /mnt/agents/output/hardware-deal-tracker/project/backend
alembic revision --autogenerate -m "Initial schema: users, tracked_items, listings, price_history, listing_scores, alerts, notification_settings"
```

The migration MUST create:
1. All 8 tables with correct columns and types
2. All foreign key constraints
3. All indexes defined in REFINED_SPEC.md Section 7.2
4. NOT NULL constraints where specified

### Task 5: Seed Data

Create `backend/scripts/seed_data.py` that inserts:
1. Default admin user (use bcrypt hash for "admin123" — Phase 2 will implement proper auth)
2. **All 34 validated tracked items** from `plan/seed_data_v2.sql` with research-backed pricing:
   - 28 original build items with updated targets
   - 6 new HDD 16TB+ items (Seagate Exos, WD Ultrastar, Toshiba MG)
   - Each item includes: name, keywords, sku, mpn, category_id, target_price, alert_threshold, search_interval, scam_floor, benchmark_median

Run it as a standalone script that can be executed:
```bash
python -m backend.scripts.seed_data
```

**Use `plan/seed_data_v2.sql`** as the authoritative seed data — it contains all 34 validated items.

### Task 6: Indexes

Ensure the following indexes exist (either in migration or add a follow-up migration):
```sql
CREATE INDEX idx_listings_marketplace_id ON listings(marketplace_id);
CREATE INDEX idx_listings_tracked_item ON listings(tracked_item_id);
CREATE INDEX idx_listings_price ON listings(price);
CREATE INDEX idx_listings_created ON listings(created_at);
CREATE INDEX idx_price_history_tracked_item ON price_history(tracked_item_id);
CREATE INDEX idx_price_history_timestamp ON price_history(timestamp);
CREATE INDEX idx_scores_listing ON listing_scores(listing_id);
CREATE INDEX idx_scores_overall ON listing_scores(overall_score DESC);
CREATE INDEX idx_alerts_pending ON alerts(was_sent) WHERE was_sent = false;
CREATE INDEX idx_alerts_created ON alerts(created_at);
```

---

## Deliverables

- [ ] `backend/app/db/base.py` — SQLAlchemy 2.0 DeclarativeBase
- [ ] `backend/app/models/*.py` — All 8 models with proper SQLAlchemy 2.0 syntax
- [ ] `backend/app/models/__init__.py` — Exports
- [ ] `backend/alembic/env.py` — Updated to use Base.metadata
- [ ] `backend/alembic/versions/` — Initial migration with all tables, FKs, indexes
- [ ] `backend/scripts/seed_data.py` — Admin user + 23 tracked items
- [ ] `backend/app/db/session.py` — Database session manager (for Phase 2):
```python
import contextlib
from typing import AsyncIterator
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from app.core.config import settings  # will be created in Phase 2

engine = create_async_engine(settings.DATABASE_URL, echo=False)
session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

@contextlib.asynccontextmanager
async def get_db_session() -> AsyncIterator[AsyncSession]:
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
```

## Git
Branch: `phase-01-database`
Base: `main` (after Phase 0 merge)
Commit message: `feat(phase-1): database schema, migrations, seed data`
