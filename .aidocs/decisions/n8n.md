# ADR — n8n removal

**Status:** Accepted
**Date:** 2026-05-27
**Phase:** MVP2 Phase 03 (Task T3.0)

## Decision

**Remove n8n** from `project/docker-compose.yml`. Delete its service block, volume, and any references in README/Tech Stack docs. Stop the running `hdt-n8n` container on docker-host-01 and drop the associated docker volume.

## Context

`hdt-n8n` has been running on docker-host-01 since 2026-05-15, unhealthy (`B4` in `DEFERRED_ISSUES.md` — the n8n image lacks `curl`, so the healthcheck always fails) and doing nothing useful (`DOC3` — no workflow JSONs exist in the repo). The original PLAN.md envisioned n8n hosting the polling cron, but Phase 01 picked APScheduler in-process (see `scheduler.md`), eliminating n8n's last remaining role in this stack.

## Rationale

- Per the homelab "remove unused services, don't rescue them" rule, fixing the healthcheck and pinning a real version on a container that has no consumers is wasted work.
- APScheduler closes G1 without n8n.
- Notification dispatch (Phase 02) goes through `app/services/notifications/*` directly — no n8n hop needed.
- n8n stays available on the broader homelab (`http://10.10.10.10:5678/api/v1` per `MEMORY.md`) for cross-project ChatOps, just not embedded in this stack.

## Implementation notes (Phase 03 T3.1)

- Delete the `n8n` service block from `project/docker-compose.yml`.
- Remove the `n8n_data` volume from the `volumes:` section.
- Update `README.md` Tech Stack table and Features list (drop "n8n workflow engine").
- On docker-host-01: `cd ~/apps/hardware-deal-tracker && docker compose stop n8n && docker compose rm -f n8n && docker volume rm <volume-name>`.
- Frees port 5678 on docker-host-01.

## Consequences

- Stack drops from 5 to 4 services. Boot is faster, dashboard `docker compose ps` is cleaner.
- If ChatOps integration ever lands for this project, it goes through the *homelab* n8n at `10.10.10.10:5678`, not an embedded instance.
