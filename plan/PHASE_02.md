# PHASE 02 — Backend Core (FastAPI + Auth + All API Endpoints)

## Objective
Build the complete FastAPI backend with JWT authentication, all CRUD endpoints, database session management, and Pydantic schemas. This is the central API that all other phases integrate with.

---

## Output Location
`/mnt/agents/output/hardware-deal-tracker/project/backend/`

---

## Dependencies
- Phase 1 (database schema) merged to `main`
- Branch from: `main`

---

## CRITICAL: API Contract Freeze
The API endpoints and Pydantic schemas defined in this phase become the **contract** that Phase 6 (Frontend) and Phase 7 (n8n) depend on. DO NOT change these without updating downstream phases.

---

## Tasks

### Task 1: Configuration (`backend/app/core/config.py`)

```python
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/hardware_tracker"
    REDIS_URL: str = "redis://localhost:6379/0"
    SECRET_KEY: str = "change-me-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # eBay
    EBAY_APP_ID: str = ""
    EBAY_CERT_ID: str = ""
    EBAY_DEV_ID: str = ""
    EBAY_REDIRECT_URI: str = ""
    
    # OpenRouter
    OPENROUTER_API_KEY: str = ""
    OPENROUTER_MODEL: str = "mistralai/mistral-small-3.1-24b-instruct"
    
    # Telegram
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_CHAT_ID: str = ""
    
    # SMTP
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    
    # App
    BACKEND_PORT: int = 8000
    LOG_LEVEL: str = "INFO"
    USE_MOCK_EBAY: bool = True
    FRONTEND_URL: str = "http://localhost:3000"
    N8N_WEBHOOK_URL: str = "http://n8n:5678/webhook"
    
    # Rate Limiting
    EBAY_DAILY_CALL_LIMIT: int = 5000
    EBAY_CALL_BUFFER: int = 200
    EBAY_NEAR_LIMIT_THRESHOLD: int = 4000
    
    class Config:
        env_file = ".env"
        case_sensitive = True

@lru_cache
def get_settings() -> Settings:
    return Settings()

settings = get_settings()
```

### Task 2: Security (`backend/app/core/security.py`)

```python
from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from passlib.context import CryptContext
from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

def verify_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError:
        return None
```

### Task 3: Database Dependencies (`backend/app/api/deps.py`)

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import session_factory
from app.models.user import User
from app.core.security import verify_token
from app.schemas.auth import TokenData

security = HTTPBearer()

async def get_db() -> AsyncSession:
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    token = verify_token(credentials.credentials)
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    
    user_id = token.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")
    
    from sqlalchemy import select
    result = await db.execute(select(User).where(User.id == int(user_id)))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")
    return user

async def get_current_admin(user: User = Depends(get_current_user)) -> User:
    if not user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return user
```

### Task 4: Pydantic Schemas

**`backend/app/schemas/auth.py`**:
```python
from pydantic import BaseModel, EmailStr

class TokenData(BaseModel):
    access_token: str
    token_type: str = "bearer"

class UserLogin(BaseModel):
    username: str
    password: str

class UserRegister(BaseModel):
    username: str
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    is_admin: bool

    class Config:
        from_attributes = True
```

**`backend/app/schemas/tracked_item.py`**:
```python
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class TrackedItemBase(BaseModel):
    name: str
    keywords: str
    sku: Optional[str] = None
    mpn: Optional[str] = None
    category_id: Optional[str] = None
    marketplace: str = "ebay"
    target_price: Optional[float] = None
    alert_threshold: float = 0.20
    min_deal_score: int = 50
    is_enabled: bool = True
    search_interval: int = 300

class TrackedItemCreate(TrackedItemBase):
    search_interval: int = 600
    scam_floor: Optional[float] = None
    benchmark_median: Optional[float] = None
    notes: Optional[str] = None

class TrackedItemUpdate(BaseModel):
    name: Optional[str] = None
    keywords: Optional[str] = None
    sku: Optional[str] = None
    mpn: Optional[str] = None
    target_price: Optional[float] = None
    alert_threshold: Optional[float] = None
    min_deal_score: Optional[int] = None
    is_enabled: Optional[bool] = None
    search_interval: Optional[int] = None
    scam_floor: Optional[float] = None
    benchmark_median: Optional[float] = None
    notes: Optional[str] = None

class TrackedItemResponse(TrackedItemBase):
    id: int
    created_at: datetime
    updated_at: datetime
    last_searched: Optional[datetime] = None
    search_interval: int
    scam_floor: Optional[float] = None
    benchmark_median: Optional[float] = None
    notes: Optional[str] = None
    priority_tier: str  # Computed from search_interval

    class Config:
        from_attributes = True

class TrackedItemWithStats(TrackedItemResponse):
    median_30d: Optional[float] = None
    lowest_30d: Optional[float] = None
    listing_count: int = 0

    class Config:
        from_attributes = True
```

**`backend/app/schemas/listing.py`**:
```python
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class ListingBase(BaseModel):
    marketplace_id: str
    title: str
    price: float
    shipping: float = 0
    seller: str
    condition: Optional[str] = None
    url: str
    image_url: Optional[str] = None
    is_auction: bool = False
    quantity: int = 1
    buying_options: Optional[List[str]] = None

class ListingCreate(ListingBase):
    tracked_item_id: Optional[int] = None
    normalized_title: Optional[str] = None
    seller_feedback: int = 0
    seller_positive_pct: float = 100.0
    condition_id: Optional[str] = None
    category_id: Optional[str] = None
    listing_date: datetime
    end_date: Optional[datetime] = None
    raw_data: Optional[dict] = None

class ListingResponse(ListingBase):
    id: int
    tracked_item_id: Optional[int] = None
    normalized_title: Optional[str] = None
    seller_feedback: int
    seller_positive_pct: float
    condition_id: Optional[str] = None
    category_id: Optional[str] = None
    listing_date: datetime
    created_at: datetime

    class Config:
        from_attributes = True
```

**`backend/app/schemas/price_history.py`**:
```python
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class PriceDataPoint(BaseModel):
    date: str  # ISO date string
    avg_price: float
    min_price: float
    max_price: float
    count: int

class PriceHistoryResponse(BaseModel):
    tracked_item_id: int
    data_points: list[PriceDataPoint]
    days: int

class PriceStatsResponse(BaseModel):
    tracked_item_id: int
    median_7d: Optional[float] = None
    median_30d: Optional[float] = None
    median_90d: Optional[float] = None
    lowest_ever: Optional[float] = None
    lowest_30d: Optional[float] = None
    highest_30d: Optional[float] = None
    volatility_30d: Optional[float] = None
    total_listings_30d: int = 0
    active_listings: int = 0
```

**`backend/app/schemas/deal.py`**:
```python
from pydantic import BaseModel
from typing import Optional
from app.schemas.listing import ListingResponse

class ScoreBreakdown(BaseModel):
    overall_score: int
    deal_score: int
    confidence: float
    classification: str
    price_zscore: Optional[float] = None
    vs_median_pct: Optional[float] = None
    vs_lowest_pct: Optional[float] = None
    est_fair_value: Optional[float] = None

class DealResponse(ListingResponse):
    score: ScoreBreakdown

class DealListResponse(BaseModel):
    deals: list[DealResponse]
    total: int
    page: int
    per_page: int
```

**`backend/app/schemas/alert.py`**:
```python
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class AlertResponse(BaseModel):
    id: int
    listing_id: int
    tracked_item_id: int
    score_id: Optional[int] = None
    channel: str
    alert_type: str
    was_sent: bool
    sent_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True

class AlertListResponse(BaseModel):
    alerts: list[AlertResponse]
    total: int
    page: int
    per_page: int
```

**`backend/app/schemas/settings.py`**:
```python
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class NotificationSettingsResponse(BaseModel):
    id: int
    user_id: int
    telegram_chat_id: Optional[str] = None
    telegram_enabled: bool = True
    email_address: Optional[str] = None
    email_enabled: bool = True
    email_digest_mode: str = "daily"
    telegram_min_score: int = 70
    email_min_score: int = 50
    mute_until: Optional[datetime] = None

    class Config:
        from_attributes = True

class NotificationSettingsUpdate(BaseModel):
    telegram_chat_id: Optional[str] = None
    telegram_enabled: Optional[bool] = None
    email_address: Optional[str] = None
    email_enabled: Optional[bool] = None
    email_digest_mode: Optional[str] = None
    telegram_min_score: Optional[int] = None
    email_min_score: Optional[int] = None
    mute_until: Optional[datetime] = None
```

### Task 5: API Endpoints

**`backend/app/api/v1/endpoints/auth.py`**:
```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.api.deps import get_db
from app.models.user import User
from app.core.security import verify_password, get_password_hash, create_access_token
from app.schemas.auth import UserLogin, UserRegister, TokenData, UserResponse

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=TokenData)
async def register(data: UserRegister, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where((User.username == data.username) | (User.email == data.email)))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Username or email already exists")
    
    user = User(
        username=data.username,
        email=data.email,
        hashed_password=get_password_hash(data.password)
    )
    db.add(user)
    await db.flush()
    token = create_access_token({"sub": str(user.id)})
    return TokenData(access_token=token)

@router.post("/login", response_model=TokenData)
async def login(data: UserLogin, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.username == data.username))
    user = result.scalar_one_or_none()
    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token({"sub": str(user.id)})
    return TokenData(access_token=token)
```

**`backend/app/api/v1/endpoints/items.py`**:
```python
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from typing import Optional
from app.api.deps import get_db, get_current_user
from app.models.tracked_item import TrackedItem
from app.models.price_history import PriceHistory
from app.schemas.tracked_item import TrackedItemCreate, TrackedItemUpdate, TrackedItemResponse, TrackedItemWithStats

router = APIRouter(prefix="/items", tags=["items"])

@router.get("", response_model=dict)
async def list_items(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    enabled: Optional[bool] = None,
    db: AsyncSession = Depends(get_db),
    user = Depends(get_current_user)
):
    query = select(TrackedItem)
    if enabled is not None:
        query = query.where(TrackedItem.is_enabled == enabled)
    
    count_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = count_result.scalar()
    
    query = query.offset((page - 1) * per_page).limit(per_page).order_by(TrackedItem.created_at.desc())
    result = await db.execute(query)
    items = result.scalars().all()
    
    return {"items": items, "total": total, "page": page, "per_page": per_page}

@router.post("", response_model=TrackedItemResponse)
async def create_item(data: TrackedItemCreate, db: AsyncSession = Depends(get_db), user = Depends(get_current_user)):
    item = TrackedItem(**data.model_dump())
    db.add(item)
    await db.flush()
    await db.refresh(item)
    return item

@router.get("/{item_id}", response_model=TrackedItemWithStats)
async def get_item(item_id: int, db: AsyncSession = Depends(get_db), user = Depends(get_current_user)):
    result = await db.execute(select(TrackedItem).where(TrackedItem.id == item_id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    # Get stats from Phase 4 (stub for now)
    return TrackedItemWithStats(
        **{k: getattr(item, k) for k in item.__dict__ if not k.startswith('_')},
        median_30d=None,
        lowest_30d=None,
        listing_count=0
    )

@router.put("/{item_id}", response_model=TrackedItemResponse)
async def update_item(item_id: int, data: TrackedItemUpdate, db: AsyncSession = Depends(get_db), user = Depends(get_current_user)):
    result = await db.execute(select(TrackedItem).where(TrackedItem.id == item_id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(item, field, value)
    await db.flush()
    await db.refresh(item)
    return item

@router.delete("/{item_id}")
async def delete_item(item_id: int, db: AsyncSession = Depends(get_db), user = Depends(get_current_user)):
    result = await db.execute(select(TrackedItem).where(TrackedItem.id == item_id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    await db.delete(item)
    return {"detail": "Item deleted"}

@router.put("/{item_id}/toggle")
async def toggle_item(item_id: int, db: AsyncSession = Depends(get_db), user = Depends(get_current_user)):
    """Quick enable/disable toggle. Returns updated item."""
    result = await db.execute(select(TrackedItem).where(TrackedItem.id == item_id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    item.is_enabled = not item.is_enabled
    await db.flush()
    await db.refresh(item)
    return {"id": item.id, "is_enabled": item.is_enabled, "status": "enabled" if item.is_enabled else "disabled"}

@router.post("/bulk-update")
async def bulk_update(
    data: dict,
    db: AsyncSession = Depends(get_db),
    user = Depends(get_current_user)
):
    """Bulk update items: { ids: [1,2,3], action: 'enable'|'disable'|'set_interval', value: optional }"""
    ids = data.get("ids", [])
    action = data.get("action", "")
    value = data.get("value")
    
    if not ids:
        raise HTTPException(status_code=400, detail="No item IDs provided")
    
    result = await db.execute(select(TrackedItem).where(TrackedItem.id.in_(ids)))
    items = result.scalars().all()
    updated = 0
    
    for item in items:
        if action == "enable":
            item.is_enabled = True
        elif action == "disable":
            item.is_enabled = False
        elif action == "set_interval" and value:
            item.search_interval = int(value)
        elif action == "delete":
            await db.delete(item)
        updated += 1
    
    await db.flush()
    return {"updated": updated, "action": action}

@router.get("/stats")
async def get_item_stats(db: AsyncSession = Depends(get_db), user = Depends(get_current_user)):
    """Return item counts by priority tier for API budget calculation."""
    from sqlalchemy import select, func, case
    result = await db.execute(
        select(
            func.count(TrackedItem.id).label("total"),
            func.sum(case((TrackedItem.search_interval <= 360, 1), else_=0)).label("p0"),
            func.sum(case((TrackedItem.search_interval.between(361, 600), 1), else_=0)).label("p1"),
            func.sum(case((TrackedItem.search_interval.between(601, 1200), 1), else_=0)).label("p2"),
            func.sum(case((TrackedItem.search_interval > 1200, 1), else_=0)).label("p3"),
            func.sum(case((TrackedItem.is_enabled == True, 1), else_=0)).label("enabled"),
        )
    )
    row = result.first()
    
    # Calculate estimated daily calls
    p0_calls = (row.p0 or 0) * 288
    p1_calls = (row.p1 or 0) * 144
    p2_calls = (row.p2 or 0) * 72
    p3_calls = (row.p3 or 0) * 48
    
    return {
        "total_items": row.total or 0,
        "enabled_items": row.enabled or 0,
        "p0_count": row.p0 or 0,
        "p1_count": row.p1 or 0,
        "p2_count": row.p2 or 0,
        "p3_count": row.p3 or 0,
        "estimated_daily_calls": p0_calls + p1_calls + p2_calls + p3_calls,
        "breakdown": {
            "p0_calls": p0_calls,
            "p1_calls": p1_calls,
            "p2_calls": p2_calls,
            "p3_calls": p3_calls
        }
    }
```

**`backend/app/api/v1/endpoints/listings.py`**:
```python
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional
from app.api.deps import get_db, get_current_user
from app.models.listing import Listing
from app.schemas.listing import ListingResponse

router = APIRouter(prefix="/listings", tags=["listings"])

@router.get("")
async def list_listings(
    item_id: Optional[int] = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    sort: str = "newest",
    db: AsyncSession = Depends(get_db),
    user = Depends(get_current_user)
):
    query = select(Listing)
    if item_id:
        query = query.where(Listing.tracked_item_id == item_id)
    
    count_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = count_result.scalar()
    
    query = query.offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(query)
    listings = result.scalars().all()
    
    return {"listings": listings, "total": total, "page": page}

@router.get("/{listing_id}", response_model=ListingResponse)
async def get_listing(listing_id: int, db: AsyncSession = Depends(get_db), user = Depends(get_current_user)):
    result = await db.execute(select(Listing).where(Listing.id == listing_id))
    listing = result.scalar_one_or_none()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    return listing
```

**`backend/app/api/v1/endpoints/history.py`**:
```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from datetime import datetime, timedelta
from app.api.deps import get_db, get_current_user
from app.models.price_history import PriceHistory
from app.models.tracked_item import TrackedItem
from app.schemas.price_history import PriceHistoryResponse, PriceDataPoint, PriceStatsResponse

router = APIRouter(prefix="/history", tags=["history"])

@router.get("/{item_id}")
async def get_history(item_id: int, days: int = 30, db: AsyncSession = Depends(get_db), user = Depends(get_current_user)):
    # Verify item exists
    result = await db.execute(select(TrackedItem).where(TrackedItem.id == item_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Item not found")
    
    since = datetime.utcnow() - timedelta(days=days)
    
    # Get daily aggregations
    # (simplified - Phase 4 will implement full historical analytics)
    return PriceHistoryResponse(tracked_item_id=item_id, data_points=[], days=days)

@router.get("/stats/{item_id}")
async def get_stats(item_id: int, db: AsyncSession = Depends(get_db), user = Depends(get_current_user)):
    result = await db.execute(select(TrackedItem).where(TrackedItem.id == item_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Item not found")
    
    return PriceStatsResponse(tracked_item_id=item_id)
```

**`backend/app/api/v1/endpoints/deals.py`**:
```python
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional
from app.api.deps import get_db, get_current_user
from app.schemas.deal import DealListResponse

router = APIRouter(prefix="/deals", tags=["deals"])

@router.get("")
async def list_deals(
    min_score: int = Query(50, ge=0, le=100),
    max_score: int = Query(100, ge=0, le=100),
    item_id: Optional[int] = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    user = Depends(get_current_user)
):
    # Returns deals with scores. Full implementation in Phase 4.
    return DealListResponse(deals=[], total=0, page=page, per_page=per_page)

@router.get("/{deal_id}")
async def get_deal(deal_id: int, db: AsyncSession = Depends(get_db), user = Depends(get_current_user)):
    from fastapi import HTTPException
    raise HTTPException(status_code=404, detail="Not yet implemented - Phase 4")
```

**`backend/app/api/v1/endpoints/alerts.py`**:
```python
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional
from app.api.deps import get_db, get_current_user
from app.models.alert import Alert
from app.schemas.alert import AlertResponse, AlertListResponse

router = APIRouter(prefix="/alerts", tags=["alerts"])

@router.get("")
async def list_alerts(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    channel: Optional[str] = None,
    sent: Optional[bool] = None,
    db: AsyncSession = Depends(get_db),
    user = Depends(get_current_user)
):
    query = select(Alert)
    if channel:
        query = query.where(Alert.channel == channel)
    if sent is not None:
        query = query.where(Alert.was_sent == sent)
    
    count_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = count_result.scalar()
    
    query = query.offset((page - 1) * per_page).limit(per_page).order_by(Alert.created_at.desc())
    result = await db.execute(query)
    alerts = result.scalars().all()
    
    return AlertListResponse(alerts=alerts, total=total, page=page, per_page=per_page)

@router.put("/{alert_id}/read")
async def mark_read(alert_id: int, db: AsyncSession = Depends(get_db), user = Depends(get_current_user)):
    result = await db.execute(select(Alert).where(Alert.id == alert_id))
    alert = result.scalar_one_or_none()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    alert.was_sent = True
    alert.sent_at = datetime.utcnow()
    await db.flush()
    return alert
```

**`backend/app/api/v1/endpoints/catalog.py`** — Hardware catalog for Add Item wizard:
```python
from fastapi import APIRouter, Depends, HTTPException, Query
from app.api.deps import get_current_user
from app.services.ebay.catalog import HardwareCatalog

router = APIRouter(prefix="/catalog", tags=["catalog"])

@router.get("")
async def search_catalog(
    q: str = Query(..., min_length=1),
    user = Depends(get_current_user)
):
    """Search hardware catalog by name, keywords, SKU, or MPN."""
    results = HardwareCatalog.search(q)
    return [{"name": r.name, "keywords": r.keywords, "sku": r.sku, "mpn": r.mpn,
             "category_id": r.category_id, "target_price": r.target_price,
             "alert_threshold": r.alert_threshold, "search_interval": r.search_interval,
             "benchmark_median": r.benchmark_median, "scam_floor": r.scam_floor,
             "notes": r.notes} for r in results[:10]]

@router.get("/categories")
async def get_categories(user = Depends(get_current_user)):
    """Return eBay categories for frontend picker."""
    return HardwareCatalog.get_categories()
```

**`backend/app/api/v1/endpoints/settings.py`**:
```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.api.deps import get_db, get_current_user
from app.models.notification_setting import NotificationSetting
from app.schemas.settings import NotificationSettingsResponse, NotificationSettingsUpdate

router = APIRouter(prefix="/settings", tags=["settings"])

@router.get("/notifications")
async def get_settings(db: AsyncSession = Depends(get_db), user = Depends(get_current_user)):
    result = await db.execute(select(NotificationSetting).where(NotificationSetting.user_id == user.id))
    settings = result.scalar_one_or_none()
    if not settings:
        settings = NotificationSetting(user_id=user.id)
        db.add(settings)
        await db.flush()
        await db.refresh(settings)
    return settings

@router.put("/notifications")
async def update_settings(
    data: NotificationSettingsUpdate,
    db: AsyncSession = Depends(get_db),
    user = Depends(get_current_user)
):
    result = await db.execute(select(NotificationSetting).where(NotificationSetting.user_id == user.id))
    settings = result.scalar_one_or_none()
    if not settings:
        raise HTTPException(status_code=404, detail="Settings not found")
    
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(settings, field, value)
    await db.flush()
    await db.refresh(settings)
    return settings
```

**`backend/app/api/v1/endpoints/search.py`**:
```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from app.api.deps import get_db, get_current_user
from app.models.tracked_item import TrackedItem

router = APIRouter(prefix="/search", tags=["search"])

@router.post("/trigger/{item_id}")
async def trigger_search(item_id: int, db: AsyncSession = Depends(get_db), user = Depends(get_current_user)):
    result = await db.execute(select(TrackedItem).where(TrackedItem.id == item_id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    # Returns stub. Phase 3 will implement actual eBay search.
    return {"listings_found": 0, "new_listings": 0, "duplicates_skipped": 0, "duration_ms": 0}

@router.post("/trigger-all")
async def trigger_all(db: AsyncSession = Depends(get_db), user = Depends(get_current_user)):
    # Returns stub. Phase 3 will implement.
    return {"items_processed": 0, "total_listings": 0, "total_new": 0, "total_duplicates": 0}

@router.get("/budget")
async def get_budget(db: AsyncSession = Depends(get_db), user = Depends(get_current_user)):
    """Get current eBay API budget status. Phase 3 implements."""
    return {
        "calls_today": 0, "daily_limit": 5000, "remaining": 5000,
        "buffer": 200, "utilization_pct": 0.0,
        "status": "ok", "searches_possible": 4800
    }

@router.get("/presets")
async def get_presets(user = Depends(get_current_user)):
    """Get polling interval presets for frontend."""
    return {
        "presets": {
            "hot": {"interval": 300, "label": "Hot (5 min)", "daily_calls": 288},
            "standard": {"interval": 600, "label": "Standard (10 min)", "daily_calls": 144},
            "monitor": {"interval": 1200, "label": "Monitor (20 min)", "daily_calls": 72},
            "passive": {"interval": 1800, "label": "Passive (30 min)", "daily_calls": 48},
        }
    }
```

**`backend/app/api/v1/router.py`** — Wire all routers:
```python
from fastapi import APIRouter
from app.api.v1.endpoints import auth, items, listings, history, deals, alerts, settings, search, catalog

router = APIRouter(prefix="/api/v1")

router.include_router(auth.router, prefix="/auth")
router.include_router(items.router, prefix="/items")
router.include_router(listings.router, prefix="/listings")
router.include_router(history.router, prefix="/history")
router.include_router(deals.router, prefix="/deals")
router.include_router(alerts.router, prefix="/alerts")
router.include_router(settings.router, prefix="/settings")
router.include_router(search.router, prefix="/search")
router.include_router(catalog.router, prefix="/catalog")

@router.get("/health")
async def health_check():
    return {"status": "healthy"}
```

### Task 6: Update main.py

**`backend/app/main.py`**:
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.router import router
from app.core.config import settings

app = FastAPI(
    title="Hardware Deal Tracker",
    description="AI-Powered Enterprise Hardware Deal Tracking API",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

@app.get("/")
async def root():
    return {"message": "Hardware Deal Tracker API", "docs": "/docs"}
```

### Task 7: Database Session Manager

**`backend/app/db/session.py`**:
```python
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.core.config import settings

engine = create_async_engine(settings.DATABASE_URL, echo=False, pool_size=10, max_overflow=20)
session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False, autoflush=False)
```

### Task 8: Tests

**`backend/tests/conftest.py`**:
```python
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.main import app
from app.db.session import session_factory as _session_factory
from app.api.deps import get_db
from app.models import Base

TEST_DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/hardware_tracker_test"

test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSession = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)

@pytest_asyncio.fixture
async def db():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with TestSession() as session:
        yield session
        await session.rollback()
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest_asyncio.fixture
async def client(db):
    async def _get_test_db():
        yield db
    app.dependency_overrides[get_db] = _get_test_db
    async with AsyncClient(app=app, base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()
```

**`backend/tests/__init__.py`** — Empty

**`backend/tests/test_auth.py`** — Test register, login, token validation

**`backend/tests/test_items.py`** — Test CRUD operations

### Task 9: Lint Configuration

**`backend/pyproject.toml`** — Add ruff configuration:
```toml
[tool.ruff]
line-length = 120
target-version = "py312"

[tool.ruff.lint]
select = ["E", "F", "W", "I", "N", "UP", "B", "C4", "SIM"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```

---

## Deliverables

- [ ] `app/core/config.py` — Pydantic settings
- [ ] `app/core/security.py` — JWT + bcrypt
- [ ] `app/db/session.py` — Async session factory
- [ ] `app/api/deps.py` — Auth + DB dependencies
- [ ] `app/schemas/*.py` — All Pydantic schemas
- [ ] `app/api/v1/endpoints/*.py` — All endpoint handlers
- [ ] `app/api/v1/router.py` — Router wiring
- [ ] `app/main.py` — Updated FastAPI app
- [ ] `tests/conftest.py` — Test fixtures
- [ ] `tests/test_auth.py` — Auth tests
- [ ] `tests/test_items.py` — Items CRUD tests
- [ ] Updated `pyproject.toml` with dev dependencies + ruff + pytest config

## Git
Branch: `phase-02-backend`
Base: `main` (after Phase 1 merge)
Commit message: `feat(phase-2): FastAPI backend, JWT auth, all CRUD endpoints, tests`
