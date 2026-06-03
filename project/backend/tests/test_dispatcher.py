"""story-T2.3: NotificationDispatcher routes scored deals to the right channels.

Covers per-channel thresholds, mute_until, the NOTIFICATIONS_ENABLED master
switch, digest deferral, and per-channel fault isolation.
"""
from datetime import datetime, timedelta

from app.core.config import settings
from app.models.listing import Listing
from app.models.notification_setting import NotificationSetting
from app.services.notifications.dispatcher import NotificationDispatcher


def _make_listing() -> Listing:
    return Listing(
        id=1,
        marketplace_id="m1",
        tracked_item_id=1,
        title="EPYC 7F72",
        price=200,
        shipping=0,
        seller="seller",
        seller_feedback=500,
        seller_positive_pct=99.0,
        url="https://www.ebay.com/itm/m1",
        listing_date=datetime.utcnow(),
    )


def _score(overall: int) -> dict:
    return {
        "overall_score": overall,
        "deal_score": overall,
        "confidence": 0.45,
        "classification": "great_deal",
        "price_zscore": -1.0,
        "vs_median_pct": 0.3,
        "vs_lowest_pct": 0.1,
        "est_fair_value": 350.0,
        "scam_warning": None,
    }


class _SpyTelegram:
    def __init__(self):
        self.calls = []

    async def send_deal_alert(self, **kwargs):
        self.calls.append(kwargs)
        return {"ok": True}


class _SpyEmail:
    def __init__(self):
        self.calls = []

    async def send_deal_alert(self, **kwargs):
        self.calls.append(kwargs)
        return True

    async def send_deal_digest(self, to, deals):
        self.calls.append({"digest_to": to, "deals": deals})
        return True


def _dispatcher():
    tg, em = _SpyTelegram(), _SpyEmail()
    return NotificationDispatcher(telegram=tg, email=em), tg, em


async def _add_setting(db, **overrides) -> NotificationSetting:
    defaults = {
        "user_id": 1,
        "telegram_chat_id": "12345",
        "telegram_enabled": True,
        "telegram_min_score": 70,
        "email_address": "me@example.com",
        "email_enabled": True,
        "email_min_score": 50,
        "email_digest_mode": "instant",
    }
    defaults.update(overrides)
    s = NotificationSetting(**defaults)
    db.add(s)
    await db.flush()
    return s


async def test_above_both_thresholds_calls_both_channels(db, monkeypatch):
    monkeypatch.setattr(settings, "NOTIFICATIONS_ENABLED", True)
    await _add_setting(db)
    disp, tg, em = _dispatcher()

    await disp.dispatch_for_deal(db, _make_listing(), _score(85))

    assert len(tg.calls) == 1
    assert len(em.calls) == 1


async def test_below_both_thresholds_calls_neither(db, monkeypatch):
    monkeypatch.setattr(settings, "NOTIFICATIONS_ENABLED", True)
    await _add_setting(db)
    disp, tg, em = _dispatcher()

    await disp.dispatch_for_deal(db, _make_listing(), _score(40))

    assert tg.calls == []
    assert em.calls == []


async def test_between_thresholds_email_only(db, monkeypatch):
    monkeypatch.setattr(settings, "NOTIFICATIONS_ENABLED", True)
    await _add_setting(db)  # tg>=70, email>=50
    disp, tg, em = _dispatcher()

    await disp.dispatch_for_deal(db, _make_listing(), _score(60))

    assert tg.calls == []
    assert len(em.calls) == 1


async def test_mute_until_suppresses_all(db, monkeypatch):
    monkeypatch.setattr(settings, "NOTIFICATIONS_ENABLED", True)
    await _add_setting(db, mute_until=datetime.utcnow() + timedelta(hours=1))
    disp, tg, em = _dispatcher()

    await disp.dispatch_for_deal(db, _make_listing(), _score(95))

    assert tg.calls == []
    assert em.calls == []


async def test_expired_mute_does_not_suppress(db, monkeypatch):
    monkeypatch.setattr(settings, "NOTIFICATIONS_ENABLED", True)
    await _add_setting(db, mute_until=datetime.utcnow() - timedelta(hours=1))
    disp, tg, em = _dispatcher()

    await disp.dispatch_for_deal(db, _make_listing(), _score(95))

    assert len(tg.calls) == 1


async def test_master_switch_off_sends_nothing(db, monkeypatch):
    monkeypatch.setattr(settings, "NOTIFICATIONS_ENABLED", False)
    await _add_setting(db)
    disp, tg, em = _dispatcher()

    await disp.dispatch_for_deal(db, _make_listing(), _score(95))

    assert tg.calls == []
    assert em.calls == []


async def test_digest_mode_defers_email(db, monkeypatch):
    monkeypatch.setattr(settings, "NOTIFICATIONS_ENABLED", True)
    await _add_setting(db, email_digest_mode="daily")
    disp, tg, em = _dispatcher()

    await disp.dispatch_for_deal(db, _make_listing(), _score(95))

    # Telegram still instant; email is deferred to the digest job (no instant send).
    assert len(tg.calls) == 1
    assert em.calls == []


async def test_disabled_channel_flags_respected(db, monkeypatch):
    monkeypatch.setattr(settings, "NOTIFICATIONS_ENABLED", True)
    await _add_setting(db, telegram_enabled=False, email_enabled=False)
    disp, tg, em = _dispatcher()

    await disp.dispatch_for_deal(db, _make_listing(), _score(95))

    assert tg.calls == []
    assert em.calls == []


async def test_failing_telegram_does_not_block_email(db, monkeypatch):
    monkeypatch.setattr(settings, "NOTIFICATIONS_ENABLED", True)
    await _add_setting(db)
    disp, tg, em = _dispatcher()

    async def _boom(**kwargs):
        raise RuntimeError("telegram down")

    tg.send_deal_alert = _boom

    # Must not raise; email still goes out despite telegram failing.
    await disp.dispatch_for_deal(db, _make_listing(), _score(95))
    assert len(em.calls) == 1


async def test_missing_chat_id_skips_telegram(db, monkeypatch):
    monkeypatch.setattr(settings, "NOTIFICATIONS_ENABLED", True)
    await _add_setting(db, telegram_chat_id=None)
    disp, tg, em = _dispatcher()

    await disp.dispatch_for_deal(db, _make_listing(), _score(95))
    assert tg.calls == []
