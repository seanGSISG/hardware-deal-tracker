"""Email digest job (story-digest).

Batches recently-scored deals above each user's ``email_min_score`` into a
single email, for users whose ``email_digest_mode`` matches the run cadence
(``daily`` / ``weekly``). Scheduled from the app lifespan under a distinct
``digest_tick`` job id (poll uses ``poll_tick``).
"""
import logging
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.listing import Listing
from app.models.listing_score import ListingScore
from app.models.notification_setting import NotificationSetting
from app.services.notifications.email import EmailClient

logger = logging.getLogger(__name__)

# How far back each cadence looks for "new since last digest".
_WINDOW = {"daily": timedelta(days=1), "weekly": timedelta(days=7)}


class DigestService:
    def __init__(self, email: EmailClient | None = None):
        self.email = email or EmailClient()

    async def run(self, db: AsyncSession, mode: str = "daily") -> int:
        """Send one digest per eligible user. Returns the number of emails sent."""
        if not settings.NOTIFICATIONS_ENABLED:
            return 0

        window = _WINDOW.get(mode)
        if window is None:
            return 0
        since = datetime.utcnow() - window

        recipients = (
            await db.execute(
                select(NotificationSetting).where(
                    NotificationSetting.email_enabled.is_(True),
                    NotificationSetting.email_digest_mode == mode,
                    NotificationSetting.email_address.is_not(None),
                )
            )
        ).scalars().all()
        if not recipients:
            return 0

        sent = 0
        for setting in recipients:
            try:
                deals = await self._recent_deals(db, since, setting.email_min_score or 0)
                if not deals:
                    continue
                ok = await self.email.send_deal_digest(setting.email_address, deals)
                if ok:
                    sent += 1
            except Exception:
                logger.exception("digest send failed (user_id=%s)", setting.user_id)
        return sent

    async def _recent_deals(self, db: AsyncSession, since: datetime, min_score: int) -> list[dict]:
        rows = (
            await db.execute(
                select(ListingScore, Listing)
                .join(Listing, Listing.id == ListingScore.listing_id)
                .where(
                    ListingScore.overall_score >= min_score,
                    ListingScore.scored_at >= since,
                )
                .order_by(ListingScore.overall_score.desc())
            )
        ).all()

        deals = []
        for score, listing in rows:
            deals.append(
                {
                    "title": listing.title,
                    "total": float(listing.price or 0) + float(listing.shipping or 0),
                    "overall_score": int(score.overall_score),
                    "classification": score.classification,
                    "url": listing.url,
                    "est_fair_value": float(score.est_fair_value) if score.est_fair_value is not None else None,
                }
            )
        return deals
