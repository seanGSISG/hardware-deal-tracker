# syntax=docker/dockerfile:1

# ---- Builder: install PRODUCTION dependencies only ----
# Dev tools (pytest/ruff/pytest-asyncio/pytest-cov/aiosqlite) are intentionally
# excluded from the image; they run in CI, not in the runtime container.
FROM python:3.12-slim AS builder

WORKDIR /app
RUN pip install --no-cache-dir uv

# Copy the full source BEFORE the editable install: setuptools resolves
# `packages = ["app"]` at build time, so the `app/` package directory must exist
# or `uv pip install -e .` fails with "package directory 'app' does not exist".
COPY . .
# Install the project's runtime deps (no [dev] extra) into the system site-packages.
# Editable install matches the original pattern but drops the dev tools.
RUN uv pip install --system --no-cache -e .

# ---- Runtime: slim image with prod deps + app code ----
FROM python:3.12-slim

WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY . .

ENV PYTHONPATH=/app
EXPOSE 8000

# Single worker on purpose: the app runs an in-process APScheduler (poll, digest,
# baseline, community-ingest) inside the FastAPI lifespan. With >1 worker each
# process starts its OWN scheduler, so jobs fire N times per interval (double
# polling / duplicate digest emails). The app is fully async and I/O-bound, so a
# single worker handles concurrent load; scale out behind a load balancer with a
# dedicated scheduler process if ever needed.
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 1"]
