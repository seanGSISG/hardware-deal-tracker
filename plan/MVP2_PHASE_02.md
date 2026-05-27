# MVP2 Phase 02 — Notifications + Auth Lockdown

**Goal:** A scored hot deal triggers Telegram + email within seconds. Registration is closed. The app refuses to start with a placeholder SECRET_KEY.

**Closes:** `G2` (notification dispatcher + missing deps), `G4` (settings auto-create on register), `S5` (close `/auth/register`), `S3` (fail-loud SECRET_KEY), `G5` (UI error toasts on failed updates).

**Exit criterion:** A test listing crafted to score above each user's `alert_threshold` fires both notification channels for the seeded admin within ≤10s of insert. `/auth/register` returns 403 unless `ALLOW_REGISTRATION=true`. Backend exits non-zero on boot if `SECRET_KEY` equals the placeholder or is unset.

---

## Dependencies

- T2.0 (deps + env wiring) blocks T2.1, T2.2
- T2.3 (dispatcher hook) blocks T2.4 (end-to-end test)
- T2.5, T2.6 are independent and can run in parallel with T2.0–T2.4

---

## Tasks

### T2.0 — Pin notification deps and env vars

Add to `project/backend/pyproject.toml`:
- `python-telegram-bot` (or just `httpx` + raw Bot API — lighter)
- `aiosmtplib`
- `jinja2` (for HTML email templates)

Wire env vars in `app/core/config.py`:
- `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`
- `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`, `SMTP_FROM`
- `NOTIFICATIONS_ENABLED` (default `true`; tests set `false`)

Update `.env.example`. Run `uv lock` and commit the updated `uv.lock`.

**Acceptance:** backend boots with the new vars; missing-but-enabled channel logs a warning (does not crash).

---

### T2.1 — Telegram service (verify / complete)

**File:** `project/backend/app/services/notifications/telegram.py`

Audit what's there. Make sure `send_deal_alert(user, deal)` formats with deal title, score, price, URL, savings %, and posts to Telegram Bot API. Honor `user.notification_settings.telegram_enabled`.

**Acceptance:** unit test mocks `httpx.AsyncClient` and asserts the call payload.

---

### T2.2 — Email service (verify / complete)

**File:** `project/backend/app/services/notifications/email.py`

HTML template via Jinja2 (`templates/emails/deal_alert.html`). Honor `user.notification_settings.email_enabled`.

**Acceptance:** unit test mocks `aiosmtplib.send` and asserts the email subject + recipient.

---

### T2.3 — Dispatcher and hook from scoring

**New file:** `project/backend/app/services/notifications/dispatcher.py`

```python
class NotificationDispatcher:
    async def dispatch_for_deal(self, deal: Deal) -> None:
        # for each user where deal.score >= user.notification_settings.alert_threshold:
        #   if telegram_enabled: TelegramService.send_deal_alert(user, deal)
        #   if email_enabled:    EmailService.send_deal_alert(user, deal)
        ...
```

Hook into the scoring path. Two options:
- **Synchronous:** call dispatcher from `DealScoringEngine.score_listing()` after persist
- **Decoupled:** emit a `deal_scored` event, dispatcher subscribes (overkill for MVP2)

Pick synchronous. Wrap each channel send in `try/except` + log so one failed channel doesn't sink the other.

**Acceptance:** integration test inserts a listing scored above threshold and asserts both mocked services were called.

---

### T2.4 — End-to-end notification smoke

With real Telegram and SMTP creds in `.env`, run a manual test: craft a listing via `POST /deals/score/{listing_id}` (or trigger the poller against a mock that returns a known-cheap item), confirm the alert lands in Telegram and inbox.

**Acceptance:** screenshots / message IDs recorded in the journal entry for this phase.

---

### T2.5 — Close `/auth/register` (S5) and auto-create settings (G4)

**File:** `project/backend/app/api/v1/endpoints/auth.py`

- Wrap registration in `if not settings.ALLOW_REGISTRATION: raise HTTPException(403, "Registration is closed")`. Default `ALLOW_REGISTRATION=false`.
- When registration *is* allowed and a user is created, also create the `notification_settings` row in the same transaction. (Or: have `PUT /settings` upsert instead of 404'ing. Pick one — auto-create at registration is cleaner.)

**Acceptance:** unit test asserts 403 when flag is false; asserts settings row exists after a successful registration when flag is true.

---

### T2.6 — Fail loud on placeholder SECRET_KEY (S3)

**File:** `project/backend/app/core/config.py` and/or `app/main.py` startup

```python
PLACEHOLDER = "change-me-in-production-min-32-chars"
if settings.SECRET_KEY == PLACEHOLDER or not settings.SECRET_KEY:
    raise RuntimeError("SECRET_KEY must be set to a non-placeholder value")
```

Remove the placeholder *default* from `docker-compose.yml` so the var is required from `.env`. Document in `.env.example` how to generate one (`openssl rand -hex 32`).

**Acceptance:** booting with the placeholder or unset value exits non-zero with a clear message.

---

### T2.7 — Frontend error toasts (G5)

**File:** `project/frontend/app/items/page.tsx` (and any sibling pages that do optimistic updates)

Wrap `toggleItem` / `deleteItem` / `updateInterval` in try/catch. On failure: revert the optimistic state change and show a toast. Reuse whatever toast library is already in the v2 UI; if none, add `sonner` (lightweight, ~5KB).

**Acceptance:** manually expire the JWT, trigger a toggle, see the toast and the row revert. Optional Playwright test if the v2 work has a Playwright harness.

---

## Verification

```bash
make test                                          # green
# manual:
ALLOW_REGISTRATION=false → POST /auth/register → 403
SECRET_KEY=change-me-in-production-min-32-chars docker compose up → backend exits non-zero
# craft hot deal, confirm Telegram + email arrive
```

Update `DEFERRED_ISSUES.md` — strike through G2, G4, G5, S3, S5.
