# PHASE 00 — Project Scaffold & Docker Compose Base

## Objective
Create the complete project directory structure, Docker Compose base, configuration files, and shared infrastructure. This is the foundation that all other phases depend on.

---

## Output Location
`/mnt/agents/output/hardware-deal-tracker/project/`

---

## Tasks

### Task 1: Create Directory Structure
Create ALL directories in the file structure defined in REFINED_SPEC.md:
```
├── docker-compose.yml
├── .env.example
├── Makefile
├── README.md
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py (stub)
│   │   ├── core/ (__init__.py)
│   │   ├── db/ (__init__.py)
│   │   ├── models/ (__init__.py)
│   │   ├── schemas/ (__init__.py)
│   │   ├── api/ (__init__.py, v1/ + __init__.py + endpoints/ + __init__.py)
│   │   └── services/ (__init__.py, ebay/, scoring/, notifications/)
│   ├── alembic/ (versions/, env.py, alembic.ini)
│   ├── tests/ (conftest.py, __init__.py)
│   ├── Dockerfile
│   ├── pyproject.toml
│   └── requirements.txt
├── frontend/
│   ├── app/ (layout.tsx stub, page.tsx stub)
│   ├── components/
│   ├── lib/
│   ├── public/
│   ├── Dockerfile
│   └── package.json
├── workflows/ (empty)
└── scripts/ (init-db.sh, seed-data.sql, healthcheck.sh)
```

### Task 2: Create Docker Compose Base
Write `docker-compose.yml` with all services:

**Services to include:**
1. **postgres** — PostgreSQL 17 with pgvector
   - Image: `postgres:17-alpine`
   - Ports: `5432:5432`
   - Volumes: `postgres_data:/var/lib/postgresql/data`
   - Environment: `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`
   - Healthcheck: `pg_isready`

2. **redis** — Redis 7
   - Image: `redis:7-alpine`
   - Ports: `6379:6379`
   - Volumes: `redis_data:/data`
   - Healthcheck: `redis-cli ping`

3. **backend** — FastAPI (Phase 2 will fill this in)
   - Build context: `./backend`
   - Ports: `8000:8000`
   - Depends on: postgres, redis
   - Environment: `DATABASE_URL`, `REDIS_URL`, `SECRET_KEY`, all eBay vars, all notification vars
   - Healthcheck: `curl -f http://localhost:8000/api/v1/health`

4. **n8n** — Workflow engine
   - Image: `n8nio/n8n:1.80`
   - Ports: `5678:5678`
   - Volumes: `n8n_data:/home/node/.n8n`
   - Environment: `DB_TYPE`, `DB_POSTGRESDB_HOST`, `DB_POSTGRESDB_DATABASE`, `DB_POSTGRESDB_USER`, `DB_POSTGRESDB_PASSWORD`, `N8N_BASIC_AUTH_USER`, `N8N_BASIC_AUTH_PASSWORD`, `N8N_ENCRYPTION_KEY`, `GENERIC_TIMEZONE`, `WEBHOOK_URL`, `N8N_PROXY_HOPS`
   - Depends on: postgres

5. **frontend** — Next.js (Phase 6 will fill this in)
   - Build context: `./frontend`
   - Ports: `3000:3000`
   - Environment: `NEXT_PUBLIC_API_URL`
   - Healthcheck: `curl -f http://localhost:3000`

### Task 3: Create `.env.example`
Write complete `.env.example` with ALL environment variables from REFINED_SPEC.md Section 13. Use placeholder values for secrets, real values for ports and non-sensitive config.

### Task 4: Create Backend Skeleton Files

**`backend/pyproject.toml`**
```toml
[project]
name = "hardware-deal-tracker"
version = "0.1.0"
description = "AI-Powered Enterprise Hardware Deal Tracker"
requires-python = ">=3.12"
dependencies = [
    "fastapi>=0.115.0",
    "uvicorn[standard]>=0.32.0",
    "sqlalchemy[asyncio]>=2.0.0",
    "asyncpg>=0.30.0",
    "alembic>=1.14.0",
    "pydantic>=2.10.0",
    "pydantic-settings>=2.6.0",
    "python-jose[cryptography]>=3.3.0",
    "passlib[bcrypt]>=1.7.4",
    "httpx>=0.28.0",
    "redis>=5.2.0",
    "python-multipart>=0.0.19",
    "email-validator>=2.2.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.3.0",
    "pytest-asyncio>=0.24.0",
    "pytest-cov>=6.0.0",
    "httpx>=0.28.0",
    "ruff>=0.8.0",
]
```

**`backend/requirements.txt`** (auto-generated from pyproject.toml dependencies)

**`backend/Dockerfile`** — Multi-stage build:
```dockerfile
# Stage 1: Builder
FROM python:3.12-slim AS builder
WORKDIR /app
COPY pyproject.toml ./
RUN pip install --no-cache-dir -e ".[dev]"

# Stage 2: Runtime
FROM python:3.12-slim
WORKDIR /app
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY . .
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
```

**`backend/app/main.py`** — Stub FastAPI app:
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Hardware Deal Tracker", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/v1/health")
async def health_check():
    return {"status": "healthy"}
```

**`backend/app/__init__.py`** — Empty file

**`backend/app/core/__init__.py`** — Empty file

**`backend/app/db/__init__.py`** — Empty file

**`backend/app/models/__init__.py`** — Empty file

**`backend/app/schemas/__init__.py`** — Empty file

**`backend/app/api/__init__.py`** — Empty file

**`backend/app/api/v1/__init__.py`** — Empty file

**`backend/app/api/v1/endpoints/__init__.py`** — Empty file

**`backend/app/api/v1/router.py`** — Stub router:
```python
from fastapi import APIRouter

router = APIRouter(prefix="/api/v1")
# Endpoints will be registered in Phase 2
```

**`backend/app/services/__init__.py`** — Empty file

**`backend/app/services/ebay/__init__.py`** — Empty file

**`backend/app/services/scoring/__init__.py`** — Empty file

**`backend/app/services/notifications/__init__.py`** — Empty file

### Task 5: Create Alembic Configuration
Write `backend/alembic/alembic.ini` with:
- `script_location = alembic`
- `sqlalchemy.url` placeholder (overridden by env.py)
- `file_template = %%(year)d_%%(month).2d_%%(day).2d_%%(rev)s_%%(slug)s`

Write `backend/alembic/env.py` (async-compatible):
```python
import asyncio
from sqlalchemy.ext.asyncio import async_engine_from_config
from alembic import context
from logging.config import fileConfig

config = context.config
if config.config_file_name:
    fileConfig(config.config_file_name)

target_metadata = None  # Will be set in Phase 1

def run_migrations_offline():
    url = config.get_main_option("sqlalchemy.url")
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True, dialect_opts={"paramstyle": "named"})
    with context.begin_transaction():
        context.run_migrations()

def do_run_migrations(connection):
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()

async def run_migrations_online():
    connectable = async_engine_from_config(config.get_section(config.config_ini_section), prefix="sqlalchemy.", poolclass=None)
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()

if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
```

### Task 6: Create Frontend Skeleton

**`frontend/package.json`**:
```json
{
  "name": "hardware-deal-tracker-frontend",
  "version": "0.1.0",
  "private": true,
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "lint": "next lint"
  },
  "dependencies": {
    "next": "^15.0.0",
    "react": "^19.0.0",
    "react-dom": "^19.0.0",
    "recharts": "^2.15.0",
    "lucide-react": "^0.460.0"
  },
  "devDependencies": {
    "@types/node": "^22.0.0",
    "@types/react": "^19.0.0",
    "typescript": "^5.6.0",
    "tailwindcss": "^4.0.0",
    "@tailwindcss/postcss": "^4.0.0",
    "eslint": "^9.0.0",
    "eslint-config-next": "^15.0.0"
  }
}
```

**`frontend/Dockerfile`**:
```dockerfile
FROM node:22-alpine
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm ci
COPY . .
RUN npm run build
EXPOSE 3000
CMD ["npm", "start"]
```

**`frontend/next.config.ts`**:
```typescript
import type { NextConfig } from 'next'
const nextConfig: NextConfig = {
  output: 'standalone',
  async rewrites() {
    return [{ source: '/api/:path*', destination: `${process.env.NEXT_PUBLIC_API_URL}/:path*` }]
  }
}
export default nextConfig
```

**`frontend/app/layout.tsx`** — Root layout stub with shadcn/ui base setup

**`frontend/app/page.tsx`** — Simple stub showing "Hardware Deal Tracker"

### Task 7: Create Scripts
Write `scripts/init-db.sh` — Wait for postgres, create DB if not exists  
Write `scripts/seed-data.sql` — Empty file (will be filled in Phase 1)  
Write `scripts/healthcheck.sh` — Check all services are healthy

### Task 8: Create Makefile
```makefile
.PHONY: up down build logs test lint migrate seed

up:
	docker compose up -d

down:
	docker compose down

build:
	docker compose build

logs:
	docker compose logs -f

test:
	docker compose exec backend pytest -xvs

migrate:
	docker compose exec backend alembic upgrade head

seed:
	docker compose exec -T postgres psql -U postgres -d hardware_tracker < scripts/seed-data.sql
```

### Task 9: Initialize Git Repository
```bash
cd /mnt/agents/output/hardware-deal-tracker/project
git init
git add -A
git commit -m "chore: project scaffold + Docker Compose base (Phase 0)"
```

---

## Deliverables

- [ ] Complete directory tree with all `__init__.py` files
- [ ] `docker-compose.yml` with 5 services (postgres, redis, backend, n8n, frontend)
- [ ] `.env.example` with all variables documented
- [ ] Backend skeleton (pyproject.toml, Dockerfile, main.py stub, alembic config)
- [ ] Frontend skeleton (package.json, Dockerfile, next.config.ts, layout.tsx)
- [ ] Scripts (init-db.sh, seed-data.sql, healthcheck.sh)
- [ ] Makefile with common commands
- [ ] Git repo initialized with first commit
- [ ] All files committed to `phase-00-scaffold` branch

## Git
Branch: `phase-00-scaffold`
Commit message: `chore(phase-0): project scaffold + Docker Compose base`
