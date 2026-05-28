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

### T2.0 — Verify deps + add missing env vars (most of this is already done)

**Preflight finding:** Notification deps and env vars are **already wired**. `config.py` already has `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`. `telegram.py` and `email.py` are **fully implemented** services (not stubs as DEFERRED_ISSUES G2 implied).

What's left:
- Add `NOTIFICATIONS_ENABLED: bool = True` to `config.py` (default `true`; tests set `false`)
- Add `SMTP_FROM: str = ""` (currently `SMTP_USER` doubles as From; cleaner to split)
- Add `jinja2` to `pyproject.toml` if not already present (T2.2 may use it for email templates; check first — `email.py` currently builds MIMEMultipart by hand)
- Update `.env.example` for the two new vars
- Run `uv lock` and commit if pyproject changed

**Acceptance:** backend boots with the new vars; missing-but-enabled channel logs a warning (does not crash).

---

### T2.1 — Telegram service (already implemented — write the test)

**Preflight:** `TelegramClient.send_deal_alert(...)` is fully implemented (emoji + markdown formatting, score classification 🔥/🎯/✅/📊/⚠️). Existing signature:

```python
async def send_deal_alert(
    title, price, shipping, total, deal_score, classification,
    seller, seller_feedback, seller_positive_pct, url,
    estimated_value=None, vs_median_pct=None, scam_warning=None,
    chat_id=None,
) -> dict
```

T2.1 is now just **write the test**: unit test mocks `httpx.AsyncClient` and asserts the call payload (chat_id, parse_mode="Markdown", body contains title + price + score). T2.3 wires the dispatcher to call it.

**Acceptance:** unit test green.

---

### T2.2 — Email service (already implemented — add deal_alert + test)

**Preflight:** `EmailClient.send_email(to, subject, html_body, text_body)` and `send_deal_digest(to, deals)` are implemented with MIMEMultipart. What's missing: a `send_deal_alert(...)` method symmetric to the Telegram one (single-deal alert vs. digest).

T2.2 work:
- Add `EmailClient.send_deal_alert(...)` taking the same fields as the Telegram one
- Optional: introduce Jinja2 template (`templates/emails/deal_alert.html`) — only if T2.0 confirmed Jinja2 was added; otherwise reuse the hand-built MIME pattern from `send_deal_digest`
- Honor `notification_setting.email_enabled` from the dispatcher (T2.3), not in the service itself

**Acceptance:** unit test mocks `aiosmtplib.send` (or whatever transport the existing `send_email` uses — verify on read) and asserts the email subject contains the deal title + score, recipient = `notification_setting.email_address`.

---

### T2.3 — Dispatcher and hook from scoring

**Preflight correction:** the `NotificationSetting` model uses **`telegram_min_score: int = 70`** and **`email_min_score: int = 50`** (per-channel thresholds) — **NOT** a single `alert_threshold`. Also: email destination is `notification_setting.email_address` (a per-setting field), not `user.email`. The model also has `mute_until: datetime` (skip dispatch entirely if `mute_until > now`) and `email_digest_mode: str = "daily"` (treat anything other than "instant" as "don't send single-deal email — let the digest cover it"; confirm behavior with Sean during implementation).

**New file:** `project/backend/app/services/notifications/dispatcher.py`

```python
class NotificationDispatcher:
    async def dispatch_for_deal(self, db: AsyncSession, listing: Listing, score: ListingScore) -> None:
        # for each user with a NotificationSetting:
        settings_list = (await db.execute(select(NotificationSetting))).scalars().all()
        for s in settings_list:
            if s.mute_until and s.mute_until > datetime.utcnow():
                continue
            if s.telegram_enabled and score.total_score >= s.telegram_min_score and s.telegram_chat_id:
                try:
                    await telegram_client.send_deal_alert(..., chat_id=s.telegram_chat_id)
                except Exception:
                    logger.exception("telegram dispatch failed")
            if s.email_enabled and score.total_score >= s.email_min_score and s.email_address:
                if s.email_digest_mode == "instant":
                    try:
                        await email_client.send_deal_alert(..., to=s.email_address)
                    except Exception:
                        logger.exception("email dispatch failed")
                # else: digest mode handles this — no single-deal send
```

Hook into the scoring path: call dispatcher from `EbayPoller.tick()` or wherever the poller calls `scorer.score()` (existing AGENTS doc references this pattern). Wrap each channel send in `try/except` + log so one failed channel doesn't sink the other.

**Acceptance:** integration test inserts a listing scored above both `telegram_min_score` and `email_min_score` and asserts both mocked services were called; another test with score below thresholds asserts neither was called.

---

### T2.4 — End-to-end notification smoke

With real Telegram and SMTP creds in `.env`, run a manual test: craft a listing via `POST /deals/score/{listing_id}` (or trigger the poller against a mock that returns a known-cheap item), confirm the alert lands in Telegram and inbox.

**Acceptance:** screenshots / message IDs recorded in the journal entry for this phase.

---

### T2.5 — Close `/auth/register` (S5) and ensure settings row exists (G4)

**File:** `project/backend/app/api/v1/endpoints/auth.py` + `endpoints/settings.py`

- Wrap registration in `if not settings.ALLOW_REGISTRATION: raise HTTPException(403, "Registration is closed")`. Default `ALLOW_REGISTRATION=false`.
- **G4 preflight finding:** `GET /settings/notifications` **already** lazy-creates the `NotificationSetting` row if missing. So a freshly-registered user who fetches their settings (which the frontend does on login) implicitly gets the row. Two fix options:
  - **A:** Make PUT `/settings/notifications` upsert too (defensive — handles direct-PUT clients)
  - **B:** Create the row in the same transaction as `User` in the register endpoint
  - **Recommended: A** — smaller change, defends against future code paths that PUT before GET; the lazy-create on GET remains the primary path.

**Acceptance:** unit test asserts `/auth/register` returns 403 when `ALLOW_REGISTRATION=false`; second test asserts PUT `/settings/notifications` succeeds against a freshly-registered user with no prior row.

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
