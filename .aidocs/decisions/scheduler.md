# ADR — Poller scheduler

**Status:** Accepted
**Date:** 2026-05-27
**Phase:** MVP2 Phase 01 (Task T1.0)

## Decision

Use **APScheduler `AsyncIOScheduler`** in-process, started in the FastAPI `lifespan`.

## Context

The poller (`EbayPoller.search_all()`) is implemented and works against the mock client, but no scheduler invokes it on an interval. MVP1 dashboard sits at zero forever. Phase 01 needs to close G1.

Three candidates were considered:

| Option | Pros | Cons |
|--------|------|------|
| APScheduler in-process | Zero new infra; ships with the backend; simplest dependency graph | Dies with the backend (acceptable — single-instance homelab) |
| n8n cron → `POST /search/trigger-all` | Reuses already-running n8n | Adds HTTP integration surface; forces keeping n8n alive in Phase 03 (currently unhealthy, slated for removal) |
| System cron + `curl` | Zero in-stack dependencies | Breaks "docker compose up = full stack"; host-side deploy step required |

## Rationale

APScheduler keeps the scheduling concern co-located with the only consumer that needs it (the backend). The "dies with the backend" downside is a non-issue: this is a single-process deployment behind Tailscale, restart on failure is handled by Docker. n8n's removal in Phase 03 (see `n8n.md`) is enabled by *not* coupling the scheduler to it. System cron was rejected because adding a host-side step undermines the reproducible-deploy story.

## Implementation notes

- Add `apscheduler` to `project/backend/pyproject.toml`; lock with `uv lock`.
- Start scheduler in `app/main.py` lifespan. Single job: `EbayPoller.search_all`, interval = `POLL_SCHEDULER_INTERVAL` (default 300s).
- The poller already respects per-item `search_interval` and the rate budget. The scheduler is a dumb tick; the poller decides which items are due.
- `SCHEDULER_ENABLED` env flag (default `true`) — tests set `false`.

## Consequences

- Phase 03 commits to *removing* n8n from the compose stack (see `n8n.md`).
- If we ever need multi-worker scheduling (we won't, for this use case), revisit with a job-store-backed APScheduler or migrate to Celery beat.
