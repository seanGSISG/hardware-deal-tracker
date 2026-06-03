# Hardware Deal Tracker

AI-Powered Enterprise Hardware Deal Tracker. Monitors eBay for deals on server-grade components (AMD EPYC CPUs, workstation GPUs, ECC memory, NVMe storage, enterprise HDDs, and more) using a tiered polling system to stay within API rate limits.

## Features

- **34 Research-Validated Items** — Curated catalog with scam floor detection and benchmark median pricing
- **Tiered Polling System** — 4 priority tiers (P0 Hot 5min → P3 Passive 30min) to fit within eBay's 5,000 calls/day limit
- **4-Layer API Protection** — Per-item intervals, Redis daily counter, priority-based skipping, hard stop at limit
- **Deal Scoring Engine** — 6-component weighted scoring (Z-score 30%, discount 25%, seller 15%, quality 15%, timing 10%, bulk 5%)
- **Scam Detection** — Automatic flagging of listings below catalog scam_floor prices
- **Add Item Wizard** — 3-step catalog auto-suggest for easy addition of new tracked items
- **Per-Item Interval Control** — Adjust polling frequency per item via the web UI
- **API Usage Dashboard** — Real-time visual tracker of eBay API call consumption
- **Multi-Channel Notifications** — Telegram bot and SMTP email alerts for hot deals
- **Full Docker Compose Stack** — PostgreSQL 17, Redis 7, FastAPI backend, Next.js 15 frontend

## Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | Next.js 15, React 19, TypeScript, Tailwind CSS v4, Recharts, Lucide Icons |
| Backend | FastAPI, async SQLAlchemy 2.0, Alembic, Pydantic v2, python-jose, passlib |
| Database | PostgreSQL 17 |
| Cache | Redis 7 (API rate budget tracking + fallback) |
| Scheduler | APScheduler (in-process tiered polling) |
| API Client | eBay Browse API (with mock client for development) |
| Notifications | Telegram Bot API, SMTP |
| Observability | Prometheus `/metrics` exporter + Grafana dashboard |

## Quick Start

### Prerequisites

- Docker Engine 24+ & Docker Compose v2
- Make (optional, for convenience commands)
- eBay Developer account (for production)
- Telegram bot (optional, for notifications)
- SMTP credentials (optional, for email alerts)

### 1. Clone & Configure

```bash
git clone <repo-url> hardware-deal-tracker
cd hardware-deal-tracker/project
cp .env.example .env
# Edit .env with your credentials (eBay API keys, Telegram, SMTP)
```

### 2. Start All Services

```bash
make up          # Build images, then start all containers in detached mode
make build       # Force rebuild all images (--no-cache)
make down        # Stop all containers
make clean       # Stop containers + remove volumes
```

> `make up` runs `docker compose build` before starting, so the backend/frontend
> images are always rebuilt from the current source. The backend is published on
> host port **8001** by default (override with `BACKEND_HOST_PORT`) to avoid
> colliding with a local vLLM/other service on 8000; inside the network it still
> listens on 8000.

Or with Docker Compose directly:

```bash
docker compose build           # Build backend + frontend images
docker compose up -d           # Start all
docker compose logs -f backend # Follow backend logs
docker compose down -v         # Stop + remove volumes
```

### 3. Initialize Database

```bash
make migrate     # Run Alembic migrations
make seed        # Seed 34 validated tracked items + admin user
make health      # Check all service health
```

### 4. Access the Application

| Service | URL |
|---------|-----|
| Frontend (Web UI) | http://localhost:3000 |
| Backend API Docs | http://localhost:8001/api/v1/docs |
| Prometheus Metrics | http://localhost:8001/metrics |

**Default admin credentials:** `admin` / `admin123`

## Architecture

### Tiered Polling System

| Priority | Interval | Items | Daily Calls |
|----------|----------|-------|-------------|
| P0 Hot | 5 min | 4 (CPU, GPU, critical) | ~1,152 |
| P1 Standard | 10 min | 10 (workstation GPUs, NVMe) | ~1,440 |
| P2 Monitor | 20 min | 12 (memory, chassis, network) | ~864 |
| P3 Passive | 30 min | 8 (HDDs, accessories) | ~384 |
| **Total** | | **34 items** | **~3,840/day (77% of 5K limit)** |

### 4-Layer API Rate Limiting

1. **Per-Item Intervals** — Each item has its own `search_interval` (configurable via UI)
2. **Redis Daily Counter** — Tracks cumulative API calls in 24h rolling window
3. **Priority-Based Skipping** — When near limit (4,000 calls), P3 → P2 → P1 items are progressively skipped
4. **Hard Stop** — Complete halt when within 200 calls of the 5,000 daily limit

### Deal Scoring (0-100)

| Component | Weight | Description |
|-----------|--------|-------------|
| Price Z-Score | 30% | How far below the moving average this price is |
| Discount Ratio | 25% | % below benchmark_median price |
| Seller Score | 15% | Seller rating + feedback count + top-rated status |
| Quality Score | 15% | Item condition (new/sealed > open box > used > for parts) |
| Timing Score | 10% | How quickly the deal is expected to sell |
| Bulk Score | 5% | Bonus for multi-quantity listings |

**Scam Floor:** Any listing priced below the catalog's `scam_floor` has its score capped at 30 and is flagged as "suspicious".

## Project Structure

```
project/
├── docker-compose.yml          # Full stack orchestration
├── .env.example                # Configuration template
├── Makefile                    # Convenience commands
├── README.md                   # This file
├── scripts/
│   ├── init-db.sh              # PostgreSQL init script
│   ├── healthcheck.sh          # Service health checker
│   └── deploy.sh               # Deployment script
├── backend/
│   ├── Dockerfile
│   ├── pyproject.toml          # Python dependencies
│   ├── alembic/                # Database migrations
│   ├── scripts/
│   │   └── seed_data_v2.sql    # 34 validated items + admin user
│   └── app/
│       ├── main.py             # FastAPI app factory
│       ├── core/
│       │   ├── config.py       # Pydantic Settings
│       │   └── security.py     # JWT auth
│       ├── db/
│       │   ├── base.py         # SQLAlchemy base model
│       │   └── session.py      # Async engine + session
│       ├── models/             # 7 SQLAlchemy models
│       ├── schemas/            # 5 Pydantic schemas
│       ├── api/
│       │   ├── deps.py         # Auth dependencies
│       │   └── v1/
│       │       ├── router.py   # API router aggregator
│       │       └── endpoints/
│       │           ├── auth.py
│       │           ├── items.py         # CRUD + toggle + bulk-update + stats
│       │           ├── deals.py
│       │           ├── alerts.py
│       │           ├── search.py
│       │           ├── settings.py
│       │           └── catalog.py       # Auto-suggest for Add Item wizard
│       └── services/
│           ├── ebay/
│           │   ├── catalog.py           # 34 validated SKUs
│           │   ├── client.py            # eBay Browse API client
│           │   ├── mock.py              # Realistic mock client (dev mode)
│           │   ├── parser.py            # Listing data normalizer
│           │   ├── dedup.py             # Duplicate detection
│           │   ├── rate_budget.py       # 4-layer rate limiter
│           │   └── poller.py            # Tiered scheduler
│           ├── scoring/
│           │   └── engine.py            # 6-component deal scorer
│           └── notifications/
│               ├── telegram.py          # Telegram bot client
│               └── email.py             # SMTP client
└── frontend/
    ├── Dockerfile
    ├── next.config.ts            # Standalone output + API rewrites
    ├── package.json
    ├── tsconfig.json
    ├── postcss.config.mjs        # Tailwind v4 PostCSS plugin
    ├── app/
    │   ├── globals.css           # Tailwind directives + base styles
    │   ├── layout.tsx            # Root layout with sidebar
    │   ├── page.tsx              # Dashboard (API usage, stats, top deals)
    │   ├── items/page.tsx        # Tracked items list + interval editor
    │   ├── items/add/page.tsx    # 3-step Add Item Wizard
    │   ├── deals/page.tsx        # Deals feed
    │   ├── alerts/page.tsx       # Alert history
    │   ├── settings/page.tsx     # Notification settings
    │   └── history/page.tsx      # Price history charts
    ├── components/
    │   ├── sidebar.tsx           # Navigation sidebar
    │   ├── stats-card.tsx        # Dashboard stat cards
    │   └── api-usage-bar.tsx     # API budget progress bar
    └── lib/
        ├── api.ts                # Backend API client
        └── hooks.ts              # React data hooks (SWR pattern)
```

## API Endpoints

All endpoints are prefixed with `/api/v1/`.

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/register` | Create new account |
| POST | `/auth/login` | Get JWT access token |
| GET | `/auth/me` | Get current user |

### Tracked Items
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/items` | List all tracked items |
| POST | `/items` | Create new item |
| GET | `/items/{id}` | Get single item |
| PUT | `/items/{id}` | Update item |
| DELETE | `/items/{id}` | Delete item |
| POST | `/items/{id}/toggle` | Enable/disable tracking |
| POST | `/items/bulk-update` | Bulk update intervals/priorities |
| GET | `/items/stats` | Summary statistics |

### Deals & Alerts
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/deals` | Get scored deals (sorted by score desc) |
| GET | `/alerts` | Get alert history |
| POST | `/alerts/{id}/dismiss` | Dismiss alert |
| GET | `/search` | Search eBay (one-off) |

### Catalog & Settings
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/catalog` | Browse hardware catalog (auto-suggest) |
| GET | `/settings` | Get notification settings |
| PUT | `/settings` | Update notification settings |

### System
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check + API usage stats |

## Development Mode

The project includes a fully functional **mock eBay client** for development without real API credentials:

```bash
# .env
USE_MOCK_EBAY=true   # Uses realistic mock listings with price variation
```

When `USE_MOCK_EBAY=true`:
- No eBay API credentials needed
- Mock client generates realistic listings with configurable price variance
- All deal scoring and alert logic works identically
- Perfect for frontend development and testing

## Make Commands

| Command | Description |
|---------|-------------|
| `make up` | Build images, then start all containers |
| `make down` | Stop all containers |
| `make build` | Rebuild all images (no cache) |
| `make logs` | Follow logs for a service (set `service=name`) |
| `make test` | Run backend tests |
| `make lint` | Run Ruff linter with auto-fix |
| `make migrate` | Run database migrations |
| `make seed` | Seed tracked items data |
| `make health` | Check service health |
| `make clean` | Stop + remove all volumes |

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `USE_MOCK_EBAY` | `true` | Use mock eBay client (dev) |
| `EBAY_APP_ID` | — | eBay App ID (production) |
| `EBAY_CERT_ID` | — | eBay Cert ID |
| `EBAY_DAILY_CALL_LIMIT` | `5000` | eBay API daily call ceiling |
| `EBAY_CALL_BUFFER` | `200` | Safety buffer before hard stop |
| `EBAY_NEAR_LIMIT_THRESHOLD` | `4000` | Start skipping low-priority items |
| `SECRET_KEY` | — | JWT signing key (min 32 chars) |
| `DATABASE_URL` | — | PostgreSQL connection string |
| `REDIS_URL` | — | Redis connection string |
| `TELEGRAM_BOT_TOKEN` | — | Telegram bot token |
| `TELEGRAM_CHAT_ID` | — | Telegram chat ID |
| `SMTP_HOST` | — | SMTP server host |
| `SMTP_USER` | — | SMTP username |
| `SMTP_PASSWORD` | — | SMTP password |

## Adding New Hardware Items

Use the **Add Item Wizard** in the web UI:
1. Navigate to **Add Item** in the sidebar
2. Search by name (auto-suggests from 34-item catalog)
3. Or select from category + component type dropdowns
4. Set target price, polling interval, and priority tier
5. If the item isn't in the catalog, fill in custom search keywords

To add items to the catalog permanently, edit `project/backend/app/services/ebay/catalog.py` and add a new `CatalogItem` entry, then run `make seed`.

## License

MIT
