# Development Guide

> Local development setup, testing, debugging, and common workflows. Read this before writing code.

---

## Prerequisites

- Docker Engine 24+ and Docker Compose v2
- Make (optional but recommended)
- Node.js 20+ (for frontend-only development)
- Python 3.12+ (for backend-only development)

---

## Quick Start (Docker — recommended)

```bash
cd project

# 1. Copy and configure environment
cp .env.example .env
# Edit .env — at minimum, set SECRET_KEY to a 32+ char string

# 2. Start all services
make up

# 3. Run migrations
make migrate

# 4. Seed data (34 validated items + admin user)
make seed

# 5. Check health
make health
```

All services should now be running:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8001/api/v1/docs (host 8001 → container 8000)

**Login:** `admin` / `admin123`

---

## Environment Setup

### Minimum `.env` for development

```env
# Required
SECRET_KEY=your-super-secret-key-min-32-characters-change-me
DATABASE_URL=postgresql+asyncpg://postgres:postgres@postgres:5432/hardware_tracker
REDIS_URL=redis://redis:6379/0

# eBay (not needed for dev — mock client is default)
USE_MOCK_EBAY=true

# Notifications (optional)
# TELEGRAM_BOT_TOKEN=...
# TELEGRAM_CHAT_ID=...
# SMTP_HOST=...
# SMTP_USER=...
# SMTP_PASSWORD=...
```

---

## Development Without Docker

### Backend Only

```bash
cd project/backend

# Install dependencies (uv manages the virtualenv)
uv sync --extra dev

# Set env vars
export DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/hardware_tracker
export REDIS_URL=redis://localhost:6379/0
export SECRET_KEY=dev-secret-key-min-32-characters-long
export USE_MOCK_EBAY=true

# Run migrations
uv run alembic upgrade head

# Start server (bare uvicorn listens on 8000; the Docker stack publishes 8001)
uv run uvicorn app.main:app --reload --port 8000
```

### Frontend Only

```bash
cd project/frontend

# Install dependencies
npm install

# Set env var (or create .env.local)
export NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1

# Start dev server
npm run dev
# → http://localhost:3000
```

---

## Make Commands Reference

| Command | Description |
|---------|-------------|
| `make up` | Start all containers in background |
| `make down` | Stop all containers |
| `make build` | Rebuild all images (no cache) |
| `make logs service=backend` | Follow logs for a service |
| `make migrate` | Run Alembic migrations |
| `make seed` | Load seed data (34 items) |
| `make test` | Run backend tests |
| `make lint` | Run Ruff linter with auto-fix |
| `make health` | Check all service health |
| `make clean` | Stop + remove all volumes (destroys data!) |

---

## Testing

### Backend Tests

```bash
# Run all tests
make test

# Run specific test file
docker compose exec backend pytest tests/test_scoring.py -xvs

# Run with coverage
docker compose exec backend pytest tests/ --cov=app --cov-report=html
```

### Test Structure

```
backend/tests/
├── conftest.py              # Shared fixtures (db session, mock client)
├── test_auth.py             # Authentication endpoints
├── test_items.py            # CRUD + bulk operations
├── test_deals.py            # Deal listing and filtering
├── test_scoring.py          # Deal scoring engine
├── test_ebay_client.py      # eBay client + mock
├── test_rate_budget.py      # Rate limiting
└── test_notifications.py    # Telegram + email
```

### Key Fixtures (conftest.py)

```python
# db_session — async database session with rollback
# mock_ebay — MockEbayClient instance
# sample_listing — pre-built Listing model
# admin_user — authenticated User model
# auth_header — valid JWT Authorization header
```

---

## Linting & Formatting

```bash
# Run linter (auto-fix)
make lint

# Or manually
docker compose exec backend ruff check . --fix
docker compose exec backend ruff format .
```

**Ruff config** (in `pyproject.toml`):
- Line length: 120
- Python target: 3.12
- Rules: E, F, W, I, N, UP, B, C4, SIM

---

## Debugging

### Backend Logs

```bash
# Follow backend logs
make logs service=backend

# All service logs
docker compose logs -f

# Just last 50 lines
docker compose logs --tail=50 backend
```

### Common Issues

| Issue | Cause | Fix |
|-------|-------|-----|
| `Backend health check fails` | Migrations not run | `make migrate` |
| `No items in frontend` | Seed not run | `make seed` |
| `Database connection refused` | Postgres not ready | Wait 10s, check `make health` |
| `Redis connection error` | Redis not started | Check `docker compose ps` |
| `JWT errors` | SECRET_KEY too short | Must be ≥32 characters |
| `eBay API errors` | No credentials + mock off | Set `USE_MOCK_EBAY=true` |
| `CORS errors` | Wrong FRONTEND_URL | Check `.env` matches actual URL |

### Reset Everything

```bash
make clean        # Stop + remove volumes (destroys all data!)
make up
make migrate
make seed
```

### Inspect Database

```bash
# Connect to Postgres
docker compose exec postgres psql -U postgres -d hardware_tracker

# Common queries
\dt                          # List tables
SELECT COUNT(*) FROM tracked_items;
SELECT * FROM listings ORDER BY created_at DESC LIMIT 10;
SELECT * FROM listing_scores ORDER BY total_score DESC LIMIT 10;
```

### Inspect Redis

```bash
docker compose exec redis redis-cli
KEYS *                       # List keys
GET ebay_api_calls_2025_01_14  # Daily call counter
TTL ebay_api_calls_2025_01_14  # Time until expiry
```

---

## Hot Reloading

### Backend

With `uvicorn --reload` (set in Docker Compose via dev override or run locally), changes to `.py` files restart the server automatically.

### Frontend

Next.js dev mode (`npm run dev`) hot-reloads both server and client components.

---

## Code Style

### Python

- **Type hints**: Required on all function signatures
- **Docstrings**: Google-style on public functions
- **Imports**: Grouped (stdlib, third-party, local), sorted
- **Naming**: `snake_case` for functions/variables, `PascalCase` for classes
- **Async**: All DB operations must be `async`/`await`

### TypeScript

- **Types**: Explicit return types on exported functions
- **Naming**: `camelCase` for functions/variables, `PascalCase` for components/types
- **Components**: Default export, function declaration style
- **Hooks**: `use` prefix, in `lib/hooks.ts`

---

## Git Workflow

Branch naming:
- `feat/description` — New features
- `fix/description` — Bug fixes
- `refactor/description` — Code refactoring
- `docs/description` — Documentation

Commit message format:
```
type(scope): description

feat(items): add bulk update endpoint
fix(scoring): correct z-score calculation
docs(readme): update setup instructions
```
