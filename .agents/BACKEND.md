# Backend Guide

> Everything about the FastAPI backend: models, API endpoints, services, and patterns. Read this when working on any Python code.

---

## Entry Points

| File | Purpose |
|------|---------|
| `backend/app/main.py` | FastAPI app factory, CORS, router inclusion |
| `backend/pyproject.toml` | Dependencies, ruff config, pytest config |
| `backend/Dockerfile` | Multi-stage build: uv install → runtime image |

---

## Core Module (`app/core/`)

### `config.py` — Settings

Uses Pydantic Settings (`pydantic-settings`) with env var fallbacks. All configuration is accessed via:

```python
from app.core.config import settings

# Examples
settings.DATABASE_URL
settings.EBAY_DAILY_CALL_LIMIT   # 5000
settings.USE_MOCK_EBAY           # True/False
settings.SECRET_KEY              # JWT signing key
```

**Adding a new setting:**
1. Add field to `Settings` class in `config.py` with type + default
2. Reference via `settings.FIELD_NAME` everywhere else
3. Add to `.env.example` with documentation comment

### `security.py` — Authentication

- `create_access_token(data)` → JWT string
- `verify_password(plain, hashed)` → bool
- `get_password_hash(password)` → bcrypt hash
- Token expiry: `ACCESS_TOKEN_EXPIRE_MINUTES` (default 30)

---

## Database (`app/db/`)

### `base.py` — SQLAlchemy Base

```python
from app.db.base import Base

class MyModel(Base):
    __tablename__ = "my_models"
```

### `session.py` — Async Engine + Session

```python
from app.db.session import AsyncSessionLocal, engine

# In endpoints (via dependency injection)
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db

@app.get("/items")
async def list_items(db: AsyncSession = Depends(get_db)):
    ...
```

---

## Models (`app/models/`)

All models inherit from `Base` (`db/base.py`). Use `mapped_column` (SQLAlchemy 2.0 style).

### Model Reference

| Model | Table | Purpose |
|-------|-------|---------|
| `User` | `users` | Authentication, single admin user |
| `TrackedItem` | `tracked_items` | Hardware items being monitored |
| `Listing` | `listings` | Individual eBay listing results |
| `ListingScore` | `listing_scores` | Deal scores for each listing |
| `PriceHistory` | `price_history` | Price snapshots over time |
| `Alert` | `alerts` | Triggered deal alerts |
| `NotificationSetting` | `notification_settings` | Telegram/SMTP config per user |

### Key Model: TrackedItem

```python
# Critical fields for AI agents to understand
class TrackedItem(Base):
    id: int                      # PK
    name: str                    # Display name
    search_keywords: str         # eBay search query
    ebay_category_id: str        # eBay category filter
    target_price: Decimal        # Alert threshold price
    search_interval: int         # Seconds between searches (default: 300)
    is_active: bool              # Enable/disable tracking
    priority_tier: str           # P0/P1/P2/P3
    scam_floor: Decimal          # Below this = suspicious
    benchmark_median: Decimal    # Used for scoring
    notes: str                   # Human-readable notes
```

**The `priority_tier` property (not a DB column, a hybrid):**
```python
@property
def priority_tier(self) -> str:
    if self.search_interval <= 300:    return "P0"  # ≤5 min
    if self.search_interval <= 600:    return "P1"  # ≤10 min
    if self.search_interval <= 1200:   return "P2"  # ≤20 min
    return "P3"                                      # >20 min
```

---

## Schemas (`app/schemas/`)

Pydantic v2 models for API request/response validation. Every endpoint uses schemas — never return raw ORM objects.

| Schema File | Covers |
|-------------|--------|
| `auth.py` | LoginRequest, Token, UserOut |
| `tracked_item.py` | TrackedItemCreate, TrackedItemUpdate, TrackedItemOut, TrackedItemStats |
| `deal.py` | DealOut, DealFilter, ScoreBreakdown |
| `settings.py` | NotificationSettingsUpdate, NotificationSettingsOut |

**Pattern for adding a new schema:**
```python
from pydantic import BaseModel, ConfigDict

class MyModelCreate(BaseModel):
    name: str
    value: int

class MyModelOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)  # Allows ORM → Pydantic
    id: int
    name: str
    value: int
```

---

## API Endpoints (`app/api/v1/endpoints/`)

### Router Registration

New endpoints are registered in `app/api/v1/router.py`:

```python
from app.api.v1.endpoints import items, deals, alerts, auth, ...

router = APIRouter()
router.include_router(items.router, prefix="/items", tags=["items"])
router.include_router(deals.router, prefix="/deals", tags=["deals"])
# ... etc
```

### Endpoint Pattern

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db, get_current_user

router = APIRouter()

@router.get("/", response_model=list[ItemOut])
async def list_items(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """List all tracked items for current user."""
    result = await db.execute(select(TrackedItem))
    items = result.scalars().all()
    return items
```

### Existing Endpoints

| Module | Routes | Key Operations |
|--------|--------|----------------|
| `auth.py` | POST `/auth/register`, `/auth/login`, GET `/auth/me` | JWT creation/validation |
| `items.py` | CRUD + POST `/toggle`, POST `/bulk-update`, GET `/stats` | Full item lifecycle |
| `deals.py` | GET `/deals`, GET `/deals/{id}` | Scored deal listing |
| `alerts.py` | GET `/alerts`, POST `/alerts/{id}/dismiss` | Alert history |
| `search.py` | GET `/search` | One-off eBay search |
| `settings.py` | GET `/settings`, PUT `/settings` | Notification config |
| `catalog.py` | GET `/catalog` | Hardware catalog browse |

### Bulk Update Endpoint

`POST /items/bulk-update` accepts:
```json
{
  "item_ids": [1, 2, 3],
  "interval": 600,        // optional
  "priority": "P1"        // optional
}
```

### Stats Endpoint

`GET /items/stats` returns:
```json
{
  "total_items": 34,
  "active_items": 32,
  "total_listings": 1247,
  "avg_deal_score": 68.5,
  "alerts_today": 3,
  "api_calls_today": 3840,
  "api_calls_limit": 5000
}
```

---

## Services (`app/services/`)

### eBay Services (`services/ebay/`)

| File | Purpose | See Also |
|------|---------|----------|
| `catalog.py` | 34 hardware SKUs with pricing metadata | [`CATALOG.md`](CATALOG.md) |
| `client.py` | Real eBay Browse API client | [`EBAY_API.md`](EBAY_API.md) |
| `mock.py` | Generates realistic mock listings for dev | [`EBAY_API.md`](EBAY_API.md) |
| `parser.py` | Normalizes raw eBay API responses | [`EBAY_API.md`](EBAY_API.md) |
| `dedup.py` | Filters duplicate listings | [`EBAY_API.md`](EBAY_API.md) |
| `rate_budget.py` | 4-layer rate limiting | [`EBAY_API.md`](EBAY_API.md) |
| `poller.py` | Async scheduler for searches | [`EBAY_API.md`](EBAY_API.md) |

### Scoring (`services/scoring/`)

| File | Purpose | See Also |
|------|---------|----------|
| `engine.py` | 6-component weighted deal scorer | [`DEAL_SCORING.md`](DEAL_SCORING.md) |

### Notifications (`services/notifications/`)

| File | Purpose |
|------|---------|
| `telegram.py` | Telegram Bot API client |
| `email.py` | SMTP client |

**Notification flow:**
1. Scoring engine flags a deal (score ≥ threshold)
2. Backend loads user's NotificationSetting
3. If Telegram configured → `TelegramClient.send_message()`
4. If SMTP configured → `EmailClient.send_email()`
5. Alert record created in `alerts` table

---

## Dependencies (`app/api/deps.py`)

| Dependency | Injects | Use |
|------------|---------|-----|
| `get_db` | `AsyncSession` | Database access in endpoints |
| `get_current_user` | `User` model | JWT auth validation |

**Always use these in endpoints** — never create sessions manually.

---

## Adding a New Feature (step-by-step)

### 1. Add/Modify a Model

```python
# app/models/my_feature.py
from app.db.base import Base
from sqlalchemy.orm import Mapped, mapped_column

class MyFeature(Base):
    __tablename__ = "my_features"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
```

### 2. Create Migration

```bash
cd backend
alembic revision --autogenerate -m "add my_feature table"
# Review the generated migration file!
```

### 3. Add Schema

```python
# app/schemas/my_feature.py
from pydantic import BaseModel, ConfigDict

class MyFeatureOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
```

### 4. Add Endpoint

```python
# app/api/v1/endpoints/my_feature.py
from fastapi import APIRouter, Depends
from app.api.deps import get_db

router = APIRouter()

@router.get("/", response_model=list[MyFeatureOut])
async def list_features(db: AsyncSession = Depends(get_db)):
    ...
```

### 5. Register Router

```python
# app/api/v1/router.py
from app.api.v1.endpoints import my_feature
router.include_router(my_feature.router, prefix="/features", tags=["features"])
```

---

## Code Quality

- **Ruff**: Linting + formatting, line-length 120, Python 3.12 target
- **Tests**: pytest + pytest-asyncio, run with `make test`
- **Type hints**: Required on all function signatures
- **Docstrings**: Required on all public functions

## Environment Variables Used by Backend

See `.env.example` in project root. Key ones:

| Variable | Default | Used In |
|----------|---------|---------|
| `DATABASE_URL` | — | `db/session.py` |
| `REDIS_URL` | — | `rate_budget.py` |
| `SECRET_KEY` | — | `security.py` |
| `USE_MOCK_EBAY` | `true` | `client.py` (switches client) |
| `EBAY_DAILY_CALL_LIMIT` | `5000` | `rate_budget.py` |
| `TELEGRAM_BOT_TOKEN` | — | `telegram.py` |
| `SMTP_HOST` | — | `email.py` |
