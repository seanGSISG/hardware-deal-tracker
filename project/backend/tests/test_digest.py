"""story-digest: DigestService batches recent deals into one email per user."""
from datetime import datetime, timedelta

from app.core.config import settings
from app.models.listing import Listing
from app.models.listing_score import ListingScore
from app.models.notification_setting import NotificationSetting
from app.models.tracked_item import TrackedItem
from app.services.notifications.digest import DigestService


class _SpyEmail:
    def __init__(self):
        self.digests = []

    async def send_deal_digest(self, to, deals):
        self.digests.append({"to": to, "deals": deals})
        return True


async def _seed_deal(db, item_id, score, scored_at=None, marketplace_id="m"):
    listing = Listing(
        marketplace_id=marketplace_id,
        tracked_item_id=item_id,
        title=f"Deal {marketplace_id}",
        price=100,
        shipping=0,
        seller="seller",
        url=f"https://ebay.com/itm/{marketplace_id}",
        listing_date=datetime.utcnow(),
    )
    db.add(listing)
    await db.flush()
    ls = ListingScore(
        listing_id=listing.id,
        tracked_item_id=item_id,
        overall_score=score,
        deal_score=score,
        confidence=0.45,
        classification="great_deal",
        est_fair_value=350,
    )
    db.add(ls)
    await db.flush()
    if scored_at is not None:
        ls.scored_at = scored_at
        await db.flush()
    return ls


async def _item(db):
    it = TrackedItem(name="EPYC", keywords="EPYC", search_interval=600, is_enabled=True)
    db.add(it)
    await db.flush()
    return it


async def test_daily_digest_batches_recent_deals_above_threshold(db, monkeypatch):
    monkeypatch.setattr(settings, "NOTIFICATIONS_ENABLED", True)
    it = await _item(db)
    db.add(NotificationSetting(user_id=1, email_address="me@test", email_enabled=True,
                               email_min_score=50, email_digest_mode="daily"))
    await db.flush()
    await _seed_deal(db, it.id, 80, marketplace_id="a")
    await _seed_deal(db, it.id, 60, marketplace_id="b")
    await _seed_deal(db, it.id, 40, marketplace_id="c")  # below threshold

    spy = _SpyEmail()
    svc = DigestService(email=spy)
    sent = await svc.run(db, mode="daily")

    assert sent == 1
    assert len(spy.digests) == 1
    assert spy.digests[0]["to"] == "me@test"
    # Only the two deals >= 50 are included.
    assert len(spy.digests[0]["deals"]) == 2


async def test_digest_skips_users_in_other_mode(db, monkeypatch):
    monkeypatch.setattr(settings, "NOTIFICATIONS_ENABLED", True)
    it = await _item(db)
    db.add(NotificationSetting(user_id=1, email_address="weekly@test", email_enabled=True,
                               email_min_score=50, email_digest_mode="weekly"))
    await db.flush()
    await _seed_deal(db, it.id, 80, marketplace_id="a")

    spy = _SpyEmail()
    svc = DigestService(email=spy)
    sent = await svc.run(db, mode="daily")
    assert sent == 0
    assert spy.digests == []


async def test_digest_excludes_old_deals(db, monkeypatch):
    monkeypatch.setattr(settings, "NOTIFICATIONS_ENABLED", True)
    it = await _item(db)
    db.add(NotificationSetting(user_id=1, email_address="me@test", email_enabled=True,
                               email_min_score=50, email_digest_mode="daily"))
    await db.flush()
    await _seed_deal(db, it.id, 80, scored_at=datetime.utcnow() - timedelta(days=3), marketplace_id="old")

    spy = _SpyEmail()
    svc = DigestService(email=spy)
    sent = await svc.run(db, mode="daily")
    # No recent deals -> no digest sent.
    assert sent == 0


async def test_digest_no_send_when_no_deals(db, monkeypatch):
    monkeypatch.setattr(settings, "NOTIFICATIONS_ENABLED", True)
    db.add(NotificationSetting(user_id=1, email_address="me@test", email_enabled=True,
                               email_min_score=50, email_digest_mode="daily"))
    await db.flush()

    spy = _SpyEmail()
    svc = DigestService(email=spy)
    assert await svc.run(db, mode="daily") == 0
    assert spy.digests == []


async def test_digest_disabled_when_notifications_off(db, monkeypatch):
    monkeypatch.setattr(settings, "NOTIFICATIONS_ENABLED", False)
    it = await _item(db)
    db.add(NotificationSetting(user_id=1, email_address="me@test", email_enabled=True,
                               email_min_score=50, email_digest_mode="daily"))
    await db.flush()
    await _seed_deal(db, it.id, 80, marketplace_id="a")

    spy = _SpyEmail()
    svc = DigestService(email=spy)
    assert await svc.run(db, mode="daily") == 0
