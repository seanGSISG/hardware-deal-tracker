# Hardware Deal Tracker — MVP2 Plan

**Version:** 2.0
**Date:** 2026-05-27
**Predecessor:** `plan/PLAN.md` (MVP1, completed 2026-05-15)
**Backlog source:** `DEFERRED_ISSUES.md` (the punted-during-MVP1 list)

---

## Why MVP2

MVP1 produced a stack that **boots, authenticates, and renders** — but the dashboard sits at zero forever because nothing schedules the poller, no notifications dispatch, and the real eBay client crashes on first call (broken f-strings). MVP2 closes those gaps so the tracker actually does the thing it claims to do, then hardens the auth surface and tightens build hygiene before this is treated as production-ready.

A Playwright-driven UI v2 iteration landed on 2026-05-21 (commit `e205bdd`): item detail route, login page, 8 new components, polished dashboard. That's already shipped — MVP2 is not about UI; it's about making the data flow real.

---

## Out of scope for MVP2

Deferred indefinitely (revisit only if the use case demands them):

- **paperless** — keep as MVP3 if at all (per Sean's stated preference for paperless as optional MVP2 elsewhere, *not here*)
- Migrating off `passlib` to `bcrypt`/`argon2-cffi` directly (`I9`) — paperline pin works
- pgvector (`B5`) — no model uses vector columns yet
- Multi-origin CORS (`S4`) — single-origin homelab demo is fine
- Frontend httpOnly cookie session (`S1`, `S2`) — Phase 2 closes registration; the localStorage token risk is acceptable behind Tailscale+CF Access
- Catalog-from-Python SQL generation (`D1` proper fix) — Phase 3 settles for keeping them in sync manually with a smoke test that diffs them
- Catalog HDD/SSD eBay category split (`D3`) — needs research; park in `.aidocs/ideas/` if it bites in Phase 1 mock-real switchover

---

## Phase index

| Phase | Theme | Deferred items closed | Exit criterion |
|-------|-------|----------------------|----------------|
| **[Phase 01](MVP2_PHASE_01.md)** | Make data flow | G1 (scheduler), B1 (eBay filter f-strings), T1 (smoke tests subset) | Real eBay API call returns listings; smoke test suite passes; listings appear in dashboard within one poll interval |
| **[Phase 02](MVP2_PHASE_02.md)** | Notifications + auth lockdown | G2 (dispatcher), G4 (settings auto-create), S5 (close registration), S3 (fail-loud SECRET_KEY), G5 (UI error toasts) | Hot-deal triggers Telegram + email; only the seeded admin can log in; missing SECRET_KEY crashes the app instead of starting with a placeholder |
| **[Phase 03](MVP2_PHASE_03.md)** | Data quality + CI + image hygiene | D1/D2 (catalog drift), B2 (server_default audit), B3 (priority_tier in list response), B4 (n8n healthcheck), I1/I2/I5/I6/I7 (compose + Dockerfile + Makefile hygiene), T2 (CI) | `make test` green in GitHub Actions on every PR; backend prod image <300MB; `make seed` idempotent; n8n healthy |

---

## Sequencing rule

**Phases run in order, not in parallel.** Each phase's exit criterion must be demonstrated (smoke test green + manual verification) before the next phase opens. This is deliberate — MVP1 was parallelized across 6 agents and that's how we ended up with 5 bugs, 5 functional gaps, and zero tests. MVP2 trades throughput for correctness.

Within a phase, tasks may run in parallel where the dependency graph allows; each phase file lists which tasks block which.

---

## Definition of "MVP2 complete"

All three phases' exit criteria green, plus:

1. `DEFERRED_ISSUES.md` updated to strike through every closed item with a one-line note ("closed Phase 0X, commit `<sha>`") and a remaining-items summary
2. `README.md` Quick Start updated (8001 port, real eBay API setup, notification env vars)
3. A new `DEFERRED_ISSUES.md` section "Punted from MVP2" lists what's still open and why
4. Journal entry filed in `~/command-center/.aidocs/journal/` and `~/command-center/.aidocs/repos/index.md` line updated to "MVP2 complete"

---

## Resolved decisions (2026-05-27)

1. **Scheduler:** APScheduler `AsyncIOScheduler` in-process — see [`.aidocs/decisions/scheduler.md`](../.aidocs/decisions/scheduler.md). Phase 01 T1.0 is now reference-only.
2. **Real eBay API credentials:** Sean has credentials arriving **by 2026-05-28** (within 24h of this plan being written). Phase 01 proceeds with mock client through T1.0–T1.3, T1.5, T1.6. **T1.4 (real-API smoke) is gated** on credentials landing; it is the last step of Phase 01 and may slip the phase exit by up to 24h. Unit-level B1 validation (T1.1 acceptance) is *not* gated on creds.
3. **n8n:** Remove from the compose stack in Phase 03 — see [`.aidocs/decisions/n8n.md`](../.aidocs/decisions/n8n.md). T3.0 is now reference-only; T3.1 unconditionally executes the removal path.
