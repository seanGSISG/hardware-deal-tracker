# MVP2 Pre-Flight Findings

**Date:** 2026-05-27
**Purpose:** De-risk Phase 01–03 execution before agentic coding begins 2026-05-28.
**Inputs:** Forensic source audit (Explore agent), external research (APScheduler + eBay Browse API via Google AI Mode), live PyPI version check.

This document **corrects plan assumptions** where the codebase or upstream reality differs from what `MVP2.md` and the phase files were written against. Read this **before** starting Phase 01.

---

## Top corrections to apply

| # | Where | Plan said | Reality | Action |
|---|-------|-----------|---------|--------|
| 1 | Phase 01 T1.3 | "Add `apscheduler` to `pyproject.toml`" | APScheduler v4 is still **alpha** (4.0.0a6, no stable). Stable = 3.11.2 (2025-12-22). The v4 API (`AsyncScheduler`, `add_schedule`, `start_in_background`) does NOT apply. | Pin `apscheduler>=3.11.2,<4`. Use v3 API. |
| 2 | Phase 01 T1.3 | "In `app/main.py` lifespan, start an `AsyncIOScheduler`" | **No lifespan exists in `main.py`**. The original AGENTS doc references the now-deprecated `@app.on_event("startup")` pattern. | T1.3 must *add* the lifespan context manager, not just register a job inside it. |
| 3 | Phase 01 T1.2 | "call `EbayPoller.search_item(item_id)` and `search_all()`" | Actual signatures: `search_item(db: AsyncSession, item: TrackedItem)` and `search_all(db: AsyncSession)`. The poller needs a db session injected through the endpoint, plus the item resolved before the call. | Update endpoint wiring to use `Depends(get_db)` + lookup item by id before calling poller. |
| 4 | Phase 02 G2 | "Notification services exist but...not yet inspected for completeness; missing `aiosmtplib` / telegram lib in `pyproject.toml`" | Both `telegram.py` and `email.py` are **fully implemented**: `TelegramClient.send_deal_alert(...)` with emoji + markdown formatting; `EmailClient.send_email(...)` + `send_deal_digest(...)` with MIMEMultipart. SMTP and httpx already wired. | Phase 02 G2 collapses to **just**: write `NotificationDispatcher` + hook from scoring. No dep work needed. |
| 5 | Phase 02 throughout | Uses `user.notification_settings.alert_threshold` and `telegram_enabled` / `email_enabled` for the dispatcher decision | Actual fields on `NotificationSetting`: `telegram_min_score: int = 70`, `email_min_score: int = 50`, `telegram_enabled: bool`, `email_enabled: bool`, `email_address: str` (per-setting, not per-User), `email_digest_mode: str = "daily"`, `mute_until: datetime`. **No `alert_threshold` field.** | Dispatcher gates each channel independently: `if telegram_enabled and score >= telegram_min_score`, `if email_enabled and score >= email_min_score`. Use `email_address` from NotificationSetting (fall back to `user.email` if not set, decide). |
| 6 | Phase 03 I1 | "Delete `version: \"3.8\"` line from docker-compose.yml" | **No `version:` line exists** in the current compose file. | Strike I1. Already done. |
| 7 | Phase 02 T2.5 G4 | "Auto-create `notification_settings` row on register" | `GET /settings/notifications` already does lazy auto-create on read (sees missing row → adds it). PUT may still 404; needs verification during implementation. | Cheaper fix: make PUT upsert. Or: leave GET-lazy-create and document, since the frontend always GETs before PUTting. Confirm during implementation. |
| 8 | Phase 03 D2 (BENCHMARK_PRICES) | "Drop `BENCHMARK_PRICES`, always read from catalog" | Confirmed: dict has 19 entries vs. catalog's 34 items. Drift exists; some keys (e.g. `"epyc 7f72": 350.0`) diverge from catalog's `benchmark_median=375`. | Refactor as planned — but also note: scoring engine currently does keyword *substring* match against this dict. Reading from the catalog directly means the scoring engine needs the `TrackedItem` object passed in, not just the listing text. |
| 9 | Phase 01 T1.1 fixture | "Unit test asserts the built filter string matches a known-good fixture" | Now we know the canonical syntax (see §"eBay Browse API canonical syntax" below). | Use these exact fixtures: `buyingOptions:{FIXED_PRICE|AUCTION}`, `conditionIds:{1000|3000}`, `price:[50..200]`, multi-filter joined by **comma**: `categoryIds:{15102},buyingOptions:{FIXED_PRICE},price:[50..200]`. |
| 10 | Phase 01 .env (eBay creds) | `EBAY_APP_ID`, `EBAY_CERT_ID`, `EBAY_DEV_ID`, `EBAY_REDIRECT_URI` env vars already exist in `config.py` | OAuth2 client_credentials flow does NOT need `EBAY_DEV_ID` or `EBAY_REDIRECT_URI` (those are legacy / for user OAuth flows). Only `EBAY_APP_ID` (client_id) and `EBAY_CERT_ID` (client_secret) are required. | Sean can register a single Browse-API-only production app tomorrow; redirect URI is irrelevant for client_credentials. |

---

## APScheduler — canonical v3.11 pattern for FastAPI

**Pin:** `apscheduler>=3.11.2,<4` (v4 is alpha — do NOT pin a beta into a real project).

### Code pattern (Python 3.12, FastAPI ≥0.109 lifespan)

```python
# app/main.py
from contextlib import asynccontextmanager
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from fastapi import FastAPI

from app.core.config import settings
from app.services.ebay.poller import EbayPoller
from app.db.session import AsyncSessionLocal

scheduler = AsyncIOScheduler()

async def _poll_tick() -> None:
    """Wrapper that opens its own db session for each tick."""
    async with AsyncSessionLocal() as db:
        poller = EbayPoller()  # construct however the existing class expects
        await poller.search_all(db)

@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings.SCHEDULER_ENABLED:
        scheduler.add_job(
            _poll_tick,
            IntervalTrigger(seconds=settings.POLL_SCHEDULER_INTERVAL),
            id="ebay-poll-tick",
            replace_existing=True,
            coalesce=True,         # collapse missed runs after downtime
            max_instances=1,       # never overlap
        )
        scheduler.start()
    yield
    if scheduler.running:
        scheduler.shutdown(wait=False)

app = FastAPI(lifespan=lifespan, ...)  # rest of existing kwargs
```

### Why these flags

- **`coalesce=True`** — if the backend was down for 30 min while interval=5min, on restart APScheduler will fire **1** catch-up tick instead of 6 simultaneous ones (which would slam Redis + DB connections). Critical for crash recovery.
- **`max_instances=1`** — the poller's `search_all` walks all 34 items and can run long. If a tick fires before the prior one finishes, the new tick is skipped (logged). Prevents overlap; matches the "tiered polling" semantics — each tick is the *opportunity* to poll, not a guarantee.
- **`replace_existing=True`** — Uvicorn `--reload` re-runs the lifespan; without this, you get `ConflictingIdError` on hot reload.
- **`shutdown(wait=False)`** — on SIGTERM, don't block container shutdown waiting for the current tick to finish. The poller is idempotent (rate budget + dedup); a half-finished tick on shutdown is recoverable.

### Env vars to add

- `SCHEDULER_ENABLED: bool = True` (default `True`; tests set `False`)
- `POLL_SCHEDULER_INTERVAL: int = 300` (seconds — matches the docstring intent from existing AGENTS doc)

---

## eBay Browse API — canonical reference (2026)

### OAuth2 client_credentials flow

| Field | Production | Sandbox |
|-------|------------|---------|
| Token endpoint | `POST https://api.ebay.com/identity/v1/oauth2/token` | `POST https://api.sandbox.ebay.com/identity/v1/oauth2/token` |
| API base | `https://api.ebay.com` | `https://api.sandbox.ebay.com` |
| Scope | `https://api.ebay.com/oauth/api_scope` | same |
| Auth header | `Authorization: Basic <base64(client_id:client_secret)>` | same |
| Body | `grant_type=client_credentials&scope=https%3A%2F%2Fapi.ebay.com%2Foauth%2Fapi_scope` | same |
| Token TTL | 7200s (2h); refresh proactively at ~6900s | same |

**Trap:** The scope is the **global** `api_scope` — there is no separate `.../buy.browse` scope. Requesting a narrower scope fails token issuance.

**Trap:** The Google-AI-Mode response listed both token URLs as `https://ebay.com` — that is **wrong**. Use the URLs in the table above.

### Filter string syntax (for `client.py` rewrite)

| Filter | Syntax | Example |
|--------|--------|---------|
| `buyingOptions` | `{VAL1\|VAL2}` — pipe-delimited, curly-brace-wrapped | `buyingOptions:{FIXED_PRICE\|AUCTION}` |
| `conditionIds` | same pattern; values are numeric | `conditionIds:{1000\|3000}` (New, Used) |
| `categoryIds` | same | `categoryIds:{15102}` |
| `price` | square brackets, two dots | `price:[50..200]` or open-ended `price:[..100]` |
| `priceCurrency` | bare value, comma-chained with price | `price:[50..200],priceCurrency:USD` |
| Multi-filter | **comma-joined** at the top level | `categoryIds:{15102},buyingOptions:{FIXED_PRICE},price:[50..200]` |

**URL-encoding:** Curly braces, pipes, square brackets, colons, and commas inside the `filter` query parameter **must** be percent-encoded when sent over the wire. Use Python's `urllib.parse.urlencode({"filter": filter_string})` — don't hand-roll the encoding.

### Condition ID reference (subset relevant to enterprise hardware)

| ID | Meaning |
|----|---------|
| 1000 | New |
| 1500 | New other (open box) |
| 2000 | Manufacturer refurbished |
| 2500 | Seller refurbished |
| 3000 | Used |
| 4000 | Very Good |
| 5000 | Good |
| 6000 | Acceptable |
| 7000 | For parts or not working |

### Rate limits

- **5,000 calls / app / day** — application-level, not per-user. (Already matches `EBAY_DAILY_CALL_LIMIT` default.)
- Throttle returns **HTTP 429** with `Retry-After: <seconds>` header. The current AGENTS doc says "back off 60s" — better to honor `Retry-After` when present, fall back to 60s if missing.
- Higher caps require eBay's *Application Growth Check* — out of scope for MVP2.

### Sean's tomorrow checklist (Browse API credentials)

1. Sign in to https://developer.ebay.com → "My Account" → "Application Keysets"
2. Create a **production** keyset for "Browse API" (sandbox is useless for our use case — sandbox listings don't match production catalog and we'd just be testing the filter syntax)
3. Copy **App ID (Client ID)** → `EBAY_APP_ID` in `.env` on docker-host-01
4. Copy **Cert ID (Client Secret)** → `EBAY_CERT_ID` in `.env`
5. **Skip** Dev ID and Redirect URI — not needed for client_credentials
6. Restart backend container: `cd ~/apps/hardware-deal-tracker && docker compose restart backend`
7. Verify token issuance: `curl -X POST -u "$EBAY_APP_ID:$EBAY_CERT_ID" -d "grant_type=client_credentials&scope=https%3A%2F%2Fapi.ebay.com%2Foauth%2Fapi_scope" https://api.ebay.com/identity/v1/oauth2/token` — should return JSON with `access_token` field
8. Only then flip `USE_MOCK_EBAY=false` and run T1.4

---

## Confirmed-as-planned (no changes needed)

These plan assumptions held up:

- ✅ B1 eBay filter f-string bug exists exactly on `client.py` lines 78/80 (curly-brace literal escape sent as literal text)
- ✅ `pyproject.toml`: `requires-python = ">=3.12"`, `pytest-asyncio>=0.24.0`, `asyncio_mode = "auto"` already in `[tool.pytest.ini_options]`
- ✅ `tests/` directory **exists** at `project/backend/tests/` — T1.5 scaffolds inside it, doesn't create it
- ✅ All B2 server_default candidates confirmed: `marketplace="ebay"`, `alert_threshold=0.20`, `min_deal_score=50`, `is_enabled=True`, `search_interval=600`, `is_active=True`. None have `server_default` currently.
- ✅ `priority_tier` is a `@property` (not `@computed_field`) on `TrackedItem`. Phase 03 T3.4 fix is correct.
- ✅ `pydantic-settings` v2 already in use. `BaseSettings` import from `pydantic_settings`.
- ✅ Existing `Settings` class already wires `SECRET_KEY`, `USE_MOCK_EBAY`, `FRONTEND_URL`, `EBAY_*`, `TELEGRAM_*`, `SMTP_*`. Only **new** vars to add: `SCHEDULER_ENABLED`, `POLL_SCHEDULER_INTERVAL`, `ALLOW_REGISTRATION`.
- ✅ `S5` — `/auth/register` is currently public (no invite/admin gate)
- ✅ `S3` — `SECRET_KEY` defaults to placeholder in `config.py`; Phase 02 T2.6 fix-on-boot logic is correct
- ✅ `docker-compose.yml` n8n volume name is `n8n_data` (used by Phase 03 T3.1 cleanup commands)

---

## Risk register for Phase 01 execution

| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| eBay credentials delayed past 2026-05-28 | Medium | T1.4 already gated; T1.0–T1.6 minus T1.4 don't need creds. Phase exit slips by however long the delay is. |
| Real-API smoke fails on first call (unknown eBay-side bug) | Low | Smoke test queries one well-known item (EPYC 7F72). If 429, honor `Retry-After`. If 401, regenerate token. If 400, inspect filter string against canonical syntax above. |
| Existing `EbayPoller` constructor needs args we don't have | Medium | Read the constructor in `poller.py` before writing `_poll_tick`. May need `RateBudgetManager`, `ListingParser`, `DeduplicationEngine` injected (per existing AGENTS doc pattern). |
| `AsyncSessionLocal` import path differs from this doc's assumption | Low | Verify `from app.db.session import AsyncSessionLocal` matches actual file. Adjust import if needed. |
| Uvicorn `--reload` doubles the scheduler | Low | `replace_existing=True` on `add_job` handles it. If the *whole scheduler* is double-instantiated by `--reload`, guard with `if not scheduler.running`. |
| Pydantic v2 deprecation warnings from `class Config` in `config.py` | Cosmetic | Migrate to `model_config = SettingsConfigDict(...)` at the same time we add the new env vars in T1.3. |

---

## Plan files to edit before execution

After this preflight is reviewed, the following targeted edits land in the same commit:

1. **`plan/MVP2_PHASE_01.md`** — T1.1 fixture spec; T1.2 db-session note; T1.3 v3 pinning + AsyncSessionLocal pattern + add (not modify) lifespan
2. **`plan/MVP2_PHASE_02.md`** — G2 collapse (services already done); use `telegram_min_score`/`email_min_score`/`email_address`; G4 PUT-upsert option
3. **`plan/MVP2_PHASE_03.md`** — Strike I1 (no `version:` line exists); reference this preflight for BENCHMARK_PRICES catalog-rewire detail
4. **`plan/MVP2.md`** — Link to this preflight from the top of the doc

After plan files are amended, MVP2 is execution-ready for 2026-05-28.
