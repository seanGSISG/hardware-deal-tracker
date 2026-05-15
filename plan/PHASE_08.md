# PHASE 08 — Docker Integration & Deployment

## Objective
Finalize the Docker Compose configuration, integrate all services, add health checks, and create deployment scripts for production-ready self-hosted deployment.

---

## Output Location
`/mnt/agents/output/hardware-deal-tracker/project/`

---

## Dependencies
- All previous phases merged to `main`
- Branch from: `main`

---

## Tasks

### Task 1: Finalize Docker Compose

Update `docker-compose.yml` with production-ready configuration:

```yaml
version: "3.8"

services:
  postgres:
    image: postgres:17-alpine
    container_name: hdt-postgres
    restart: unless-stopped
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./scripts/init-db.sh:/docker-entrypoint-initdb.d/init-db.sh
      - ./scripts/seed-data.sql:/docker-entrypoint-initdb.d/seed-data.sql
    environment:
      POSTGRES_DB: ${POSTGRES_DB:-hardware_tracker}
      POSTGRES_USER: ${POSTGRES_USER:-postgres}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-postgres}
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U $$POSTGRES_USER -d $$POSTGRES_DB"]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 10s
    networks:
      - hdt-network

  redis:
    image: redis:7-alpine
    container_name: hdt-redis
    restart: unless-stopped
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes --maxmemory 256mb --maxmemory-policy allkeys-lru
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - hdt-network

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: hdt-backend
    restart: unless-stopped
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: ${DATABASE_URL:-postgresql+asyncpg://postgres:postgres@postgres:5432/hardware_tracker}
      REDIS_URL: ${REDIS_URL:-redis://redis:6379/0}
      SECRET_KEY: ${SECRET_KEY:-change-me-in-production}
      ALGORITHM: ${ALGORITHM:-HS256}
      ACCESS_TOKEN_EXPIRE_MINUTES: ${ACCESS_TOKEN_EXPIRE_MINUTES:-30}
      EBAY_APP_ID: ${EBAY_APP_ID:-}
      EBAY_CERT_ID: ${EBAY_CERT_ID:-}
      EBAY_DEV_ID: ${EBAY_DEV_ID:-}
      EBAY_REDIRECT_URI: ${EBAY_REDIRECT_URI:-}
      OPENROUTER_API_KEY: ${OPENROUTER_API_KEY:-}
      OPENROUTER_MODEL: ${OPENROUTER_MODEL:-mistralai/mistral-small-3.1-24b-instruct}
      TELEGRAM_BOT_TOKEN: ${TELEGRAM_BOT_TOKEN:-}
      TELEGRAM_CHAT_ID: ${TELEGRAM_CHAT_ID:-}
      SMTP_HOST: ${SMTP_HOST:-}
      SMTP_PORT: ${SMTP_PORT:-587}
      SMTP_USER: ${SMTP_USER:-}
      SMTP_PASSWORD: ${SMTP_PASSWORD:-}
      USE_MOCK_EBAY: ${USE_MOCK_EBAY:-true}
      LOG_LEVEL: ${LOG_LEVEL:-INFO}
      FRONTEND_URL: ${FRONTEND_URL:-http://localhost:3000}
      N8N_WEBHOOK_URL: ${N8N_WEBHOOK_URL:-http://n8n:5678/webhook}
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/v1/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s
    networks:
      - hdt-network

  n8n:
    image: n8nio/n8n:1.80
    container_name: hdt-n8n
    restart: unless-stopped
    ports:
      - "5678:5678"
    volumes:
      - n8n_data:/home/node/.n8n
      - ./workflows:/workflows:ro
    environment:
      DB_TYPE: postgresdb
      DB_POSTGRESDB_HOST: postgres
      DB_POSTGRESDB_DATABASE: ${POSTGRES_DB:-hardware_tracker}
      DB_POSTGRESDB_USER: ${POSTGRES_USER:-postgres}
      DB_POSTGRESDB_PASSWORD: ${POSTGRES_PASSWORD:-postgres}
      N8N_BASIC_AUTH_ACTIVE: "true"
      N8N_BASIC_AUTH_USER: ${N8N_BASIC_AUTH_USER:-admin}
      N8N_BASIC_AUTH_PASSWORD: ${N8N_BASIC_AUTH_PASSWORD:-admin}
      N8N_ENCRYPTION_KEY: ${N8N_ENCRYPTION_KEY:-change-me-in-production}
      GENERIC_TIMEZONE: ${GENERIC_TIMEZONE:-UTC}
      WEBHOOK_URL: ${WEBHOOK_URL:-http://localhost:5678/}
      N8N_PROXY_HOPS: "1"
      EXECUTIONS_DATA_PRUNE: "true"
      EXECUTIONS_DATA_MAX_AGE: "168"
    depends_on:
      postgres:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5678/healthz"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s
    networks:
      - hdt-network

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    container_name: hdt-frontend
    restart: unless-stopped
    ports:
      - "3000:3000"
    environment:
      NEXT_PUBLIC_API_URL: ${NEXT_PUBLIC_API_URL:-http://localhost:8000/api/v1}
    depends_on:
      backend:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3000"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s
    networks:
      - hdt-network

volumes:
  postgres_data:
    driver: local
  redis_data:
    driver: local
  n8n_data:
    driver: local

networks:
  hdt-network:
    driver: bridge
```

### Task 2: Backend Dockerfile (Production)

Update `backend/Dockerfile`:

```dockerfile
# Builder stage
FROM python:3.12-slim AS builder

WORKDIR /app
RUN pip install --no-cache-dir uv

COPY pyproject.toml ./
RUN uv pip install --system -e ".[dev]"

# Production stage
FROM python:3.12-slim AS production

WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY . .

# Run migrations on startup
ENV PYTHONPATH=/app
EXPOSE 8000

CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2"]
```

### Task 3: Frontend Dockerfile (Production)

Update `frontend/Dockerfile`:

```dockerfile
FROM node:22-alpine AS builder

WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm ci
COPY . .
RUN npm run build

FROM node:22-alpine AS production

WORKDIR /app
ENV NODE_ENV=production
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
COPY --from=builder /app/public ./public

EXPOSE 3000
CMD ["node", "server.js"]
```

### Task 4: Health Check Scripts

**`scripts/healthcheck.sh`**:
```bash
#!/bin/bash
set -e

echo "Hardware Deal Tracker — Health Check"
echo "===================================="

check_service() {
    local name=$1
    local url=$2
    if curl -sf "$url" > /dev/null 2>&1; then
        echo "✅ $name: healthy"
        return 0
    else
        echo "❌ $name: unhealthy"
        return 1
    fi
}

check_service "PostgreSQL" "http://localhost:8000/api/v1/health"
check_service "Backend API" "http://localhost:8000/api/v1/health"
check_service "n8n" "http://localhost:5678/healthz"
check_service "Frontend" "http://localhost:3000"

echo ""
echo "Redis check:"
docker compose exec redis redis-cli ping 2>/dev/null && echo "✅ Redis: healthy" || echo "❌ Redis: unhealthy"
```

### Task 5: Database Init Script

**`scripts/init-db.sh`**:
```bash
#!/bin/bash
set -e

echo "Initializing Hardware Deal Tracker database..."

# Wait for PostgreSQL to be ready
until pg_isready -U "$POSTGRES_USER" -d "$POSTGRES_DB"; do
    echo "Waiting for PostgreSQL..."
    sleep 2
done

# Enable pgvector extension
echo "Enabling pgvector extension..."
psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "CREATE EXTENSION IF NOT EXISTS vector;"

echo "Database initialization complete!"
```

### Task 6: Reverse Proxy Configuration

**`docker-compose.proxy.yml`** (optional overlay for Traefik):

```yaml
version: "3.8"

services:
  traefik:
    image: traefik:v3.2
    container_name: hdt-traefik
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - ./traefik:/etc/traefik
    command:
      - --api.insecure=true
      - --providers.docker=true
      - --providers.docker.exposedbydefault=false
      - --entrypoints.web.address=:80
    networks:
      - hdt-network

  frontend:
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.frontend.rule=Host(`localhost`)"
      - "traefik.http.routers.frontend.entrypoints=web"
      - "traefik.http.services.frontend.loadbalancer.server.port=3000"

  backend:
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.backend.rule=Host(`localhost`) && PathPrefix(`/api`)"
      - "traefik.http.routers.backend.entrypoints=web"
      - "traefik.http.services.backend.loadbalancer.server.port=8000"

  n8n:
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.n8n.rule=Host(`n8n.localhost`)"
      - "traefik.http.routers.n8n.entrypoints=web"
      - "traefik.http.services.n8n.loadbalancer.server.port=5678"
```

### Task 7: Environment Configuration

**`.env.example`** (complete):
```bash
# Database
POSTGRES_DB=hardware_tracker
POSTGRES_USER=postgres
POSTGRES_PASSWORD=change-me-in-production
DATABASE_URL=postgresql+asyncpg://postgres:change-me-in-production@postgres:5432/hardware_tracker

# Backend
SECRET_KEY=your-super-secret-key-min-32-characters-long
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
BACKEND_PORT=8000

# Redis
REDIS_URL=redis://redis:6379/0

# eBay API (required for production)
EBAY_APP_ID=your-ebay-app-id
EBAY_CERT_ID=your-ebay-cert-id
EBAY_DEV_ID=your-ebay-dev-id
EBAY_REDIRECT_URI=your-ebay-redirect-uri

# OpenRouter AI (optional)
OPENROUTER_API_KEY=your-openrouter-api-key
OPENROUTER_MODEL=mistralai/mistral-small-3.1-24b-instruct

# Telegram (optional)
TELEGRAM_BOT_TOKEN=your-bot-token
TELEGRAM_CHAT_ID=your-chat-id

# SMTP (optional)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# n8n
N8N_BASIC_AUTH_USER=admin
N8N_BASIC_AUTH_PASSWORD=change-me
N8N_ENCRYPTION_KEY=another-encryption-key
GENERIC_TIMEZONE=America/New_York
WEBHOOK_URL=https://your-domain.com/

# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1

# Application
USE_MOCK_EBAY=true
LOG_LEVEL=INFO
FRONTEND_URL=http://localhost:3000
```

### Task 8: Deployment Script

**`scripts/deploy.sh`**:
```bash
#!/bin/bash
set -e

echo "🚀 Hardware Deal Tracker — Deployment"
echo "====================================="

# Check prerequisites
command -v docker >/dev/null 2>&1 || { echo "❌ Docker is required but not installed."; exit 1; }
command -v docker-compose >/dev/null 2>&1 || { echo "❌ Docker Compose is required but not installed."; exit 1; }

# Check .env
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Copying from .env.example..."
    cp .env.example .env
    echo "⚠️  Please edit .env with your configuration before proceeding."
    exit 1
fi

echo "📦 Building images..."
docker-compose build

echo "🗄️ Starting database..."
docker-compose up -d postgres redis

sleep 5

echo "🔄 Running database migrations..."
docker-compose run --rm backend alembic upgrade head

echo "🌱 Seeding initial data..."
docker-compose exec -T postgres psql -U postgres -d hardware_tracker < scripts/seed-data.sql 2>/dev/null || true

echo "🚀 Starting all services..."
docker-compose up -d

echo ""
echo "✅ Deployment complete!"
echo ""
echo "Services:"
echo "  Frontend:  http://localhost:3000"
echo "  Backend:   http://localhost:8000/api/v1/docs"
echo "  n8n:       http://localhost:5678"
echo "  Postgres:  localhost:5432"
echo "  Redis:     localhost:6379"
echo ""
echo "Run './scripts/healthcheck.sh' to verify all services."
```

### Task 9: Log Streaming Script

**`scripts/logs.sh`**:
```bash
#!/bin/bash
SERVICE=${1:-all}

case $SERVICE in
    backend) docker-compose logs -f backend ;;
    frontend) docker-compose logs -f frontend ;;
    n8n) docker-compose logs -f n8n ;;
    postgres) docker-compose logs -f postgres ;;
    redis) docker-compose logs -f redis ;;
    *) docker-compose logs -f ;;
esac
```

### Task 10: Backup Script

**`scripts/backup.sh`**:
```bash
#!/bin/bash
BACKUP_DIR="./backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
mkdir -p "$BACKUP_DIR"

echo "Creating backup..."
docker-compose exec -T postgres pg_dump -U postgres hardware_tracker > "$BACKUP_DIR/db_backup_$TIMESTAMP.sql"
echo "Backup saved to $BACKUP_DIR/db_backup_$TIMESTAMP.sql"
```

---

## Deliverables

- [ ] `docker-compose.yml` — Production-ready with health checks
- [ ] `docker-compose.proxy.yml` — Optional Traefik overlay
- [ ] `backend/Dockerfile` — Multi-stage Python build
- [ ] `frontend/Dockerfile` — Multi-stage Node.js build
- [ ] `scripts/healthcheck.sh` — Service health verification
- [ ] `scripts/init-db.sh` — Database initialization
- [ ] `scripts/deploy.sh` — Full deployment automation
- [ ] `scripts/logs.sh` — Log streaming
- [ ] `scripts/backup.sh` — Database backup
- [ ] `.env.example` — Complete environment template
- [ ] All scripts made executable (`chmod +x scripts/*.sh`)

## Git
Branch: `phase-08-deploy`
Base: `main` (all previous phases merged)
Commit message: `feat(phase-8): Docker Compose finalization, deployment scripts, health checks`
