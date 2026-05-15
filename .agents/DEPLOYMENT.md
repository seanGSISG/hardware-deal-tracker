# Deployment Guide

> Docker Compose orchestration, production configuration, and infrastructure. Read this when deploying or modifying the stack.

---

## Architecture

5 services orchestrated by Docker Compose:

```
┌─────────────────────────────────────────────┐
│            Docker Compose Network            │
│                                             │
│  ┌──────────┐   ┌──────────┐   ┌────────┐  │
│  │ Frontend │   │ Backend  │   │   n8n  │  │
│  │  :3000   │   │  :8000   │   │ :5678  │  │
│  └────┬─────┘   └────┬─────┘   └───┬────┘  │
│       │              │              │       │
│       └──────────────┼──────────────┘       │
│                      │                      │
│              ┌───────┴───────┐              │
│              │   PostgreSQL   │              │
│              │     :5432      │              │
│              └───────┬───────┘              │
│                      │                      │
│              ┌───────┴───────┐              │
│              │     Redis      │              │
│              │     :6379      │              │
│              └───────────────┘              │
└─────────────────────────────────────────────┘
```

---

## Service Definitions

### PostgreSQL 17

- **Image:** `postgres:17-alpine`
- **Port:** 5432 (host) → 5432 (container)
- **Volume:** `postgres_data` (persistent)
- **Init:** `scripts/init-db.sh` mounted to `/docker-entrypoint-initdb.d/`
- **Healthcheck:** `pg_isready`

### Redis 7

- **Image:** `redis:7-alpine`
- **Port:** 6379 (host) → 6379 (container)
- **Volume:** `redis_data` (persistent)
- **Config:** AOF persistence, 256MB maxmemory, LRU eviction
- **Healthcheck:** `redis-cli ping`

### Backend (FastAPI)

- **Build:** `backend/Dockerfile` (multi-stage: uv install → runtime)
- **Port:** 8000
- **Startup:** `alembic upgrade head && uvicorn app.main:app --workers 2`
- **Depends on:** PostgreSQL (healthy), Redis (healthy)
- **Healthcheck:** `GET /api/v1/health`

### Frontend (Next.js)

- **Build:** `frontend/Dockerfile` (multi-stage: npm ci → standalone)
- **Port:** 3000
- **Output:** `standalone` (self-contained Node.js server)
- **Depends on:** Backend (healthy)
- **Rewrites:** `/api/*` → backend API

### n8n

- **Image:** `n8nio/n8n:1.80`
- **Port:** 5678
- **Database:** Uses same PostgreSQL instance
- **Auth:** Basic auth (configured in `.env`)
- **Depends on:** PostgreSQL (healthy)

---

## Startup Order

Docker Compose `depends_on` with `condition: service_healthy` ensures:

```
Phase 1: postgres, redis   (parallel, must pass health checks)
Phase 2: backend           (waits for Phase 1)
Phase 3: n8n               (waits for postgres)
Phase 4: frontend          (waits for backend)
```

**Total cold-start time:** ~30-60 seconds depending on hardware.

---

## Docker Compose Configuration

### Volumes

| Volume | Purpose | Backup |
|--------|---------|--------|
| `postgres_data` | All application data | `pg_dump` via `make backup` |
| `redis_data` | Rate counters, dedup cache | Optional (resets daily) |
| `n8n_data` | Workflow definitions | Export from n8n UI |

### Networks

- Single bridge network: `hdt-network`
- All services can resolve each other by service name (`postgres`, `redis`, `backend`, etc.)

---

## Production Checklist

### 1. Environment Variables

Copy `.env.example` to `.env` and configure ALL of these:

```env
# REQUIRED — Security
SECRET_KEY=<64-char random string>

# REQUIRED — Database (change password!)
POSTGRES_PASSWORD=<strong-password>
DATABASE_URL=postgresql+asyncpg://postgres:<strong-password>@postgres:5432/hardware_tracker

# REQUIRED — Production eBay credentials
USE_MOCK_EBAY=false
EBAY_APP_ID=<your-ebay-app-id>
EBAY_CERT_ID=<your-ebay-cert-id>

# RECOMMENDED — Notifications (at least one)
TELEGRAM_BOT_TOKEN=<bot-token>
TELEGRAM_CHAT_ID=<chat-id>
# OR
SMTP_HOST=<smtp-host>
SMTP_USER=<email>
SMTP_PASSWORD=<app-password>

# n8n security
N8N_BASIC_AUTH_PASSWORD=<strong-password>
N8N_ENCRYPTION_KEY=<32-char-random>
```

### 2. SSL/HTTPS

Place a reverse proxy (nginx, Traefik, Caddy) in front:

```
Internet → Reverse Proxy (443) → Frontend (3000)
                              → Backend (8000)
                              → n8n (5678)
```

Update `FRONTEND_URL` and `NEXT_PUBLIC_API_URL` to use `https://`.

### 3. Firewall

Expose only:
- 443 (HTTPS via reverse proxy)
- Maybe 22 (SSH)

Do NOT expose:
- 5432 (PostgreSQL) — internal only
- 6379 (Redis) — internal only
- 8000 (Backend) — proxied through frontend rewrites
- 5678 (n8n) — proxied or VPN-only

### 4. Backups

```bash
# Automated daily backup (add to crontab)
0 2 * * * cd /path/to/project && make backup

# Backups saved as: backup-YYYYMMDD-HHMMSS.sql
```

### 5. Monitoring

Health endpoints:
- Backend: `GET /api/v1/health`
- n8n: `GET /healthz`

Monitor these with Uptime Kuma, Pingdom, or similar.

### 6. Log Rotation

Docker Compose handles container log rotation via `log-opt`:

```yaml
# Add to each service in docker-compose.yml
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
```

---

## Deploy Script (`scripts/deploy.sh`)

```bash
# Reads .env, builds images, starts in dependency order
make deploy
# Or directly:
sh scripts/deploy.sh
```

Steps:
1. Check `.env` exists
2. `docker compose build`
3. Start `postgres` + `redis`
4. Wait for PostgreSQL
5. Start `backend`
6. Start all remaining services

---

## Updating

### Rolling Update (zero-downtime-ish)

```bash
# Pull new code
git pull origin main

# Rebuild and restart (staggered by dependency order)
make build
make up
make migrate  # If there are new migrations
```

### Database Migrations

Always run migrations AFTER the new code is deployed but BEFORE old code is fully stopped:

```bash
# 1. Deploy new backend image
docker compose up -d backend

# 2. Run migrations
docker compose exec backend alembic upgrade head

# 3. Verify
curl http://localhost:8000/api/v1/health
```

---

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| `backend unhealthy` | Migrations pending | `make migrate` |
| `frontend unhealthy` | Backend not ready | Wait, check `make health` |
| `database connection refused` | Wrong DATABASE_URL | Check `.env` matches Docker service name |
| `CORS errors` | Wrong FRONTEND_URL | Must match actual frontend origin |
| `Redis errors` | Redis not started | `docker compose up -d redis` |
| `API calls not working` | USE_MOCK_EBAY=false but no credentials | Set `USE_MOCK_EBAY=true` or add eBay creds |
| `n8n won't start` | Encryption key changed | Reset `N8N_ENCRYPTION_KEY` to original value |

---

## Resource Requirements

| Service | CPU | Memory | Storage |
|---------|-----|--------|---------|
| PostgreSQL | 0.5 | 512MB | 10GB+ (grows with price history) |
| Redis | 0.1 | 256MB | 1GB |
| Backend | 0.5 | 256MB | Minimal |
| Frontend | 0.1 | 128MB | Minimal |
| n8n | 0.5 | 512MB | 5GB |
| **Total** | **~1.7** | **~1.6GB** | **~16GB** |

Recommended minimum: **2 vCPU, 2GB RAM, 20GB SSD**.
