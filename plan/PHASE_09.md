# PHASE 09 — End-to-End Testing & QA

## Objective
Write comprehensive end-to-end tests, smoke tests for all services, and final documentation. Ensure the entire stack works together correctly.

---

## Output Location
`/mnt/agents/output/hardware-deal-tracker/project/`

---

## Dependencies
- All previous phases merged to `main`
- Branch from: `main`

---

## Tasks

### Task 1: Backend E2E Tests

**`backend/tests/e2e/`** — Integration tests that test the full flow:

**`backend/tests/e2e/__init__.py`** — Empty  
**`backend/tests/e2e/test_full_pipeline.py`**:
```python
import pytest
from datetime import datetime, timedelta
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.main import app
from app.models.tracked_item import TrackedItem
from app.models.listing import Listing
from app.models.listing_score import ListingScore
from app.models.alert import Alert
from app.services.ebay.poller import EbayPoller
from app.services.scoring import DealScoringEngine
from app.services.notifications.dispatcher import AlertDispatcher

class TestFullPipeline:
    """End-to-end test of the complete deal tracking pipeline."""
    
    @pytest.mark.asyncio
    async def test_search_tracked_item(self, client: AsyncClient, db: AsyncSession):
        """Step 1: Search eBay for a tracked item and store listings."""
        # Create a test tracked item
        item = TrackedItem(
            name="AMD EPYC 7F72",
            keywords="AMD EPYC 7F72 server CPU",
            sku="100-000000336",
            mpn="7F72",
            target_price=300.00,
            is_enabled=True
        )
        db.add(item)
        await db.flush()
        
        # Trigger search via API
        response = await client.post(f"/api/v1/search/trigger/{item.id}")
        assert response.status_code == 200
        data = response.json()
        assert "listings_found" in data
        
        # Verify listings stored
        result = await db.execute(select(Listing).where(Listing.tracked_item_id == item.id))
        listings = result.scalars().all()
        assert len(listings) > 0
    
    @pytest.mark.asyncio
    async def test_score_listing(self, client: AsyncClient, db: AsyncSession):
        """Step 2: Score a listing and verify score calculation."""
        # Create test listing
        listing = Listing(
            marketplace_id="test_score_1",
            title="AMD EPYC 7F72 24-Core TESTED",
            price=250.00,
            shipping=9.99,
            seller="test_seller",
            seller_feedback=1500,
            seller_positive_pct=99.2,
            condition="Used",
            url="https://ebay.com/itm/test",
            listing_date=datetime.utcnow()
        )
        db.add(listing)
        await db.flush()
        
        # Score via API
        response = await client.post(f"/api/v1/deals/score/{listing.id}")
        assert response.status_code == 200
        data = response.json()
        
        assert 0 <= data["overall_score"] <= 100
        assert 0 <= data["deal_score"] <= 100
        assert 0 < data["confidence"] <= 1
        assert data["classification"] in ["hot_deal", "great_deal", "good_deal", "fair_deal", "poor_deal"]
    
    @pytest.mark.asyncio
    async def test_full_flow(self, client: AsyncClient, db: AsyncSession):
        """Step 3: Complete pipeline — search → store → score → alert."""
        # 1. Create tracked item
        item = TrackedItem(
            name="NVIDIA T4 GPU",
            keywords="NVIDIA T4 GPU inference accelerator",
            target_price=150.00,
            is_enabled=True
        )
        db.add(item)
        await db.flush()
        
        # 2. Search
        search_resp = await client.post(f"/api/v1/search/trigger/{item.id}")
        assert search_resp.status_code == 200
        
        # 3. Get stored listings
        listings_resp = await client.get(f"/api/v1/listings?item_id={item.id}")
        assert listings_resp.status_code == 200
        listings_data = listings_resp.json()
        assert listings_data["total"] > 0
        
        first_listing = listings_data["listings"][0]
        
        # 4. Score the listing
        score_resp = await client.post(f"/api/v1/deals/score/{first_listing['id']}")
        assert score_resp.status_code == 200
        
        # 5. Verify score stored
        deals_resp = await client.get("/api/v1/deals?min_score=1")
        assert deals_resp.status_code == 200
        deals_data = deals_resp.json()
        assert deals_data["total"] > 0
    
    @pytest.mark.asyncio
    async def test_deal_filters(self, client: AsyncClient):
        """Test deal filtering by score range."""
        # Get all deals
        resp_all = await client.get("/api/v1/deals?min_score=0&max_score=100")
        assert resp_all.status_code == 200
        
        # Filter high scores only
        resp_high = await client.get("/api/v1/deals?min_score=80")
        assert resp_high.status_code == 200
        data = resp_high.json()
        for deal in data.get("deals", []):
            score = deal.get("score", {})
            assert score.get("overall_score", 0) >= 80
    
    @pytest.mark.asyncio
    async def test_price_history_api(self, client: AsyncClient, db: AsyncSession):
        """Test price history endpoints."""
        # Create tracked item
        item = TrackedItem(name="Test Item", keywords="test keywords")
        db.add(item)
        await db.flush()
        
        # Get history (empty)
        resp = await client.get(f"/api/v1/history/{item.id}?days=30")
        assert resp.status_code == 200
        data = resp.json()
        assert data["tracked_item_id"] == item.id
        assert "data_points" in data
        
        # Get stats (empty)
        resp = await client.get(f"/api/v1/history/stats/{item.id}")
        assert resp.status_code == 200
```

### Task 2: Smoke Tests (`backend/tests/e2e/test_smoke.py`)

```python
import pytest
from httpx import AsyncClient

class TestSmoke:
    """Quick smoke tests for all services."""
    
    @pytest.mark.asyncio
    async def test_health(self, client: AsyncClient):
        resp = await client.get("/api/v1/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "healthy"
    
    @pytest.mark.asyncio
    async def test_auth_flow(self, client: AsyncClient):
        # Register
        reg = await client.post("/api/v1/auth/register", json={
            "username": "testuser",
            "email": "test@test.com",
            "password": "testpass123"
        })
        assert reg.status_code == 200
        token = reg.json()["access_token"]
        assert token
        
        # Login
        login = await client.post("/api/v1/auth/login", json={
            "username": "testuser",
            "password": "testpass123"
        })
        assert login.status_code == 200
        assert login.json()["access_token"]
    
    @pytest.mark.asyncio
    async def test_items_crud(self, client: AsyncClient):
        # Register and get token
        reg = await client.post("/api/v1/auth/register", json={
            "username": "testuser2",
            "email": "test2@test.com",
            "password": "testpass123"
        })
        token = reg.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Create
        create = await client.post("/api/v1/items", json={
            "name": "Test CPU",
            "keywords": "test cpu",
            "target_price": 100.00
        }, headers=headers)
        assert create.status_code == 200
        item_id = create.json()["id"]
        
        # Read
        read = await client.get(f"/api/v1/items/{item_id}", headers=headers)
        assert read.status_code == 200
        assert read.json()["name"] == "Test CPU"
        
        # Update
        update = await client.put(f"/api/v1/items/{item_id}", json={
            "target_price": 150.00
        }, headers=headers)
        assert update.status_code == 200
        assert update.json()["target_price"] == 150.00
        
        # Delete
        delete = await client.delete(f"/api/v1/items/{item_id}", headers=headers)
        assert delete.status_code == 200
```

### Task 3: Test Utilities

**`backend/tests/e2e/conftest.py`**:
```python
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.main import app
from app.db.session import session_factory as _session_factory
from app.api.deps import get_db
from app.models import Base
from app.core.security import get_password_hash
from app.models.user import User

TEST_DB_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/hardware_tracker_test"

test_engine = create_async_engine(TEST_DB_URL, echo=False)
TestSession = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)

@pytest_asyncio.fixture(scope="function")
async def db():
    """Create a fresh test database for each test."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    
    async with TestSession() as session:
        # Seed default admin
        admin = User(username="admin", email="admin@test.com", hashed_password=get_password_hash("admin123"), is_admin=True)
        session.add(admin)
        await session.commit()
        yield session
        await session.rollback()
    
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest_asyncio.fixture
async def client(db):
    """Create a test client with overridden DB dependency."""
    async def _get_test_db():
        yield db
    
    app.dependency_overrides[get_db] = _get_test_db
    async with AsyncClient(app=app, base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()

@pytest_asyncio.fixture
async def auth_client(client):
    """Create an authenticated test client."""
    resp = await client.post("/api/v1/auth/login", json={"username": "admin", "password": "admin123"})
    token = resp.json()["access_token"]
    client.headers = {"Authorization": f"Bearer {token}"}
    yield client
```

### Task 4: Load Test Script

**`scripts/load-test.sh`**:
```bash
#!/bin/bash
API_URL="${API_URL:-http://localhost:8000/api/v1}"
CONCURRENT=${CONCURRENT:-10}
REQUESTS=${REQUESTS:-100}

echo "Load Testing Hardware Deal Tracker API"
echo "URL: $API_URL"
echo "Concurrent: $CONCURRENT, Requests: $REQUESTS"

# Install hey if not present
command -v hey >/dev/null 2>&1 || go install github.com/rakyll/hey@latest

# Test health endpoint
echo ""
echo "Testing /health..."
hey -n $REQUESTS -c $CONCURRENT "$API_URL/health"

# Test items list (requires auth)
echo ""
echo "Testing /items..."
hey -n $REQUESTS -c $CONCURRENT -H "Authorization: Bearer test-token" "$API_URL/items"
```

### Task 5: Documentation

**`README.md`**:
```markdown
# Hardware Deal Tracker

AI-Powered Enterprise Hardware Deal Tracking Platform.

## Quick Start

```bash
# 1. Clone and setup
cp .env.example .env
# Edit .env with your configuration

# 2. Deploy
./scripts/deploy.sh

# 3. Access
# Frontend: http://localhost:3000
# API Docs: http://localhost:8000/api/v1/docs
# n8n:      http://localhost:5678
```

## Architecture

- **Frontend**: Next.js 15 + Tailwind CSS + shadcn/ui
- **Backend**: FastAPI + SQLAlchemy 2.0 + asyncpg
- **Database**: PostgreSQL 17 + pgvector
- **Cache**: Redis 7
- **Workflows**: n8n

## Development

See `plan/` directory for detailed phase-by-phase development plans.

## License

MIT
```

### Task 6: Makefile

Update `Makefile` with all targets:

```makefile
.PHONY: all up down build logs test lint migrate seed deploy health backup clean e2e

all: up migrate seed

up:
	@echo "Starting services..."
	docker compose up -d

down:
	@echo "Stopping services..."
	docker compose down

build:
	@echo "Building images..."
	docker compose build --no-cache

logs:
	@./scripts/logs.sh $(service)

test:
	@echo "Running unit tests..."
	docker compose exec backend pytest tests/ -xvs

e2e:
	@echo "Running E2E tests..."
	docker compose exec backend pytest tests/e2e/ -xvs

lint:
	@echo "Linting..."
	docker compose exec backend ruff check . --fix

migrate:
	@echo "Running migrations..."
	docker compose exec backend alembic upgrade head

seed:
	@echo "Seeding data..."
	docker compose exec -T postgres psql -U postgres -d hardware_tracker < scripts/seed-data.sql

deploy:
	@./scripts/deploy.sh

health:
	@./scripts/healthcheck.sh

backup:
	@./scripts/backup.sh

clean: down
	@echo "Removing volumes..."
	docker compose down -v
	docker system prune -f
```

---

## Deliverables

- [ ] `tests/e2e/conftest.py` — E2E test fixtures with test DB
- [ ] `tests/e2e/test_smoke.py` — Smoke tests for all endpoints
- [ ] `tests/e2e/test_full_pipeline.py` — End-to-end pipeline test
- [ ] `scripts/load-test.sh` — Performance/load testing
- [ ] `README.md` — Complete project documentation
- [ ] `Makefile` — All development and deployment commands
- [ ] All tests passing (`pytest tests/ -xvs`)
- [ ] Code coverage report (target: >80%)

## Git
Branch: `phase-09-testing`
Base: `main` (all phases merged)
Commit message: `test(phase-9): e2e tests, smoke tests, documentation, Makefile`

## Final Merge
After this branch passes all tests, merge to `main` as `v0.1.0`:
```bash
git tag -a v0.1.0 -m "MVP Release: Hardware Deal Tracker v0.1.0"
```
