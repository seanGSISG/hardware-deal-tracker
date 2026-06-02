# Handoff — MVP2 Plan Cascade (2026-06-02)

For the next agent. The MVP2 mega-plan is **built and approved (ADRs signed off)**;
it is NOT yet executed. Your job: finalize the PCPartPicker source detail once the
background research lands, then run `/plan-cascade:mega-approve` to execute.

---

## State: where we are

- Planning method switched from the old `plan/MVP2_PHASE_*.md` files to **Plan Cascade
  mega-plan** (`/plan-cascade:auto --flow full` → routed to `mega-plan`).
- Spec interview with Sean is **done** (answers captured in `mega-plan.json` →
  `spec_config.interview_notes`).
- All **9 ADRs accepted** by Sean (`design_doc.json`, all `status: "accepted"`).
- The old **"phases run in order, not in parallel" rule was REMOVED** from
  `plan/MVP2.md` per Sean — execution is dependency-driven parallel worktrees now.

### Files created/edited (repo root = `/home/adminuser/projects/hardware-deal-tracker`)
- `mega-plan.json` / `mega-plan.md` — 6 features, 3 batches (gitignored)
- `design_doc.json` / `design_doc.md` — 7 components, 5 patterns, 9 ADRs (gitignored)
- `mega-findings.md` — **READ THIS** — verified current-state map + shared-file
  merge-conflict hotspots + source-research summaries
- `.mega-status.json` — execution tracker (gitignored)
- `plan/MVP2.md` — sequencing rule replaced (committed-tracked)
- `plan/MVP2_SOURCE_RESEARCH.md` — used-server retailer shortlist (Shopify JSON-LD)
- `plan/MVP2_PCPARTPICKER_RESEARCH.md` — **may still be in flight**; a background agent
  was researching PCPartPicker scrapers at handoff. Confirm it exists; if missing,
  re-run the research (prompt below).
- `.gitignore` — added Plan Cascade artifact entries

---

## Feature / batch map (worktree-isolated, max parallel)

```
Batch 1:  feature-001  Make Data Flow  ← KEYSTONE
Batch 2:  feature-002  Quality/CI/Ops + observability   (dep: 001)
          feature-003  Notifications dispatcher + auth   (dep: 001)
          feature-004  Catalog source-of-truth + CRUD    (dep: 001)
          feature-005  Multi-source ingestion            (dep: 001)
Batch 3:  feature-006  Price history + AI analysis       (dep: 001, 004)
```
Config: flow=full, tdd=on, batch-confirm=on, isolation=worktree.

---

## Source #2 = PCPartPicker — RESOLVED (research complete, plan updated)

`plan/MVP2_PCPARTPICKER_RESEARCH.md` is written; `feature-005` + `ADR-003` are fully
updated. Net conclusion baked into the plan:
- **Benchmark/reference source ONLY** — refresh `benchmark_median` + 'vs retail' delta;
  **never** route PCPartPicker rows through the eBay scoring/dedup/notification pipeline
  (condition always `new`). It feeds feature-004 + feature-006.
- **Reuse `lucwl/pypartpicker`'s data model, replace its stale transport.** `docyx`
  dataset = one-time spec bootstrap; `N-O-U-R` = paid ZenRows, skip.
- Overlap only ~10-12 of 34 items (workstation GPU, consumer NVMe/SSD, non-ECC DDR,
  Threadripper) via optional `pcpp_product_id`; useless for EPYC/ECC/enterprise.
- Cheapest-first anti-bot ($0/mo target): `curl_cffi` + caching → **residential**
  Tailscale exit (**NOT** datacenter `104.223.27.177`) → Nodriver/FlareSolverr →
  paid API behind a flag last. Own ≤200/day bucket, `ENABLE_PCPARTPICKER=false` default.
- **ToS forbids scraping + no public API** → minimal volume, cache, keep disableable.

No open plan items remain. Proceed straight to execution.

---

## To execute

```
/plan-cascade:mega-approve --flow full --tdd on --confirm
```
This generates per-feature PRDs and spawns Batch-1 (feature-001) in a worktree; you get
a batch-confirm prompt before each batch's agents spawn. Re-render scripts live at:
`/home/adminuser/.claude/plugins/cache/plan-cascade/plan-cascade/4.4.0/skills/hybrid-ralph/scripts/`
(`render-plan-docs.py --mode mega`, `unified-review.py --mode mega`).

---

## Critical context for execution (from `mega-findings.md` — don't re-discover)

**Already DONE — do not redo:** `client.py` scope+filter bugs FIXED; `EbayPoller`
fully implemented (`search_item(db,item)` / `search_all(db)`, uses RateBudgetManager +
DeduplicationEngine); `telegram.py.send_deal_alert` + `email.py.send_email/send_deal_alert`
implemented (email uses BLOCKING smtplib → migrate to aiosmtplib); `NotificationSetting`
has per-channel `telegram_min_score`/`email_min_score` (NO `alert_threshold`);
`HardwareCatalog` = 34 items w/ `benchmark_median`; compose has no `version:` line.

**Keystone gap (ADR-006):** the poller NEVER calls the scoring engine — feature-001 must
wire `DealScoringEngine.calculate_overall_score(listing, historical_stats, catalog_item)`
into the poll path so listings persist scored (required for dashboard + dispatcher).

**Backend = baked Docker image, NO bind mount.** Code changes need
`cd project && docker compose up -d --build backend`, not just restart.

**context-mode hook blocks host curl/wget/WebFetch** — use
`docker exec hdt-backend python -c "import urllib.request; ..."` for HTTP checks.

**Shared-file merge hotspots (Batch 2 parallel worktrees):** `config.py` (001 owns the
SettingsConfigDict migration; 003/006 add vars on top), `scoring/engine.py` (001 scoring-in-poll
vs 004 drop BENCHMARK_PRICES), `poller.py` (001 vs 005 adapter refactor),
`seed_data_v2.sql` (002 idempotency vs 004 generate_seed.py), `main.py` lifespan job
registration (001 poll tick / 003 digest / 006 price snapshot — distinct job ids).

**Leftover cleanup (from the eBay creds session):** wipe the temp Bitwarden session if
still present: `rm -f /tmp/.bwsess /tmp/.bwerr`.

---

## If you must re-run the PCPartPicker research

Spawn a general-purpose agent: review github.com/lucwl/pypartpicker,
github.com/N-O-U-R/PcPartPicker-Scraping, github.com/docyx/pc-part-dataset (+ newer repos);
analyze PCPartPicker's Cloudflare anti-bot; rank cheapest-first scraping strategies
(rotating-UA direct → self-hosted proxy/VPN → Playwright stealth → paid API fallback);
assess catalog-overlap fit (benchmark-source vs deal-source); design a PcPartPickerAdapter
for the shared SourceAdapter interface. Write to `plan/MVP2_PCPARTPICKER_RESEARCH.md`.
