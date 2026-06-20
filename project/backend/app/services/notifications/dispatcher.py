"""Notification dispatcher (T2.3).

Fans a freshly-scored deal out to each user's configured notification channels,
honouring per-channel score thresholds, the ``mute_until`` window, and the
``NOTIFICATIONS_ENABLED`` master switch. Each channel is isolated in its own
try/except so one failing transport never sinks the others, and the whole call
is best-effort: it must never raise into the poll/score path.
"""
import logging
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.listing import Listing
from app.models.notification_setting import NotificationSetting
from app.services.notifications.email import EmailClient
from app.services.notifications.ntfy import NtfyClient
from app.services.notifications.telegram import TelegramClient

logger = logging.getLogger(__name__)


class NotificationDispatcher:
    """Routes a scored deal to Telegram, ntfy, and/or email per NotificationSetting rows."""

    def __init__(
        self,
        telegram: TelegramClient | None = None,
        email: EmailClient | None = None,
        ntfy: NtfyClient | None = None,
    ):
        self.telegram = telegram or TelegramClient()
        self.email = email or EmailClient()
        self.ntfy = ntfy or NtfyClient()

    async def dispatch_for_deal(self, db: AsyncSession, listing: Listing, score: dict) -> dict:
        """Best-effort dispatch for one scored listing. Never raises."""
        result = {"telegram_sent": 0, "ntfy_sent": 0, "email_sent": 0, "email_deferred": 0}
        if not settings.NOTIFICATIONS_ENABLED:
            return result

        overall = int(score.get("overall_score", 0))
        now = datetime.utcnow()

        try:
            rows = (await db.execute(select(NotificationSetting))).scalars().all()
        except Exception:
            logger.exception("dispatch: failed to load notification settings")
            return result

        for setting in rows:
            if setting.mute_until and _aware_to_naive(setting.mute_until) > now:
                continue

            # --- Telegram (always instant) ---
            if (
                setting.telegram_enabled
                and setting.telegram_chat_id
                and overall >= (setting.telegram_min_score or 0)
            ):
                try:
                    await self.telegram.send_deal_alert(
                        title=listing.title,
                        price=float(listing.price),
                        shipping=float(listing.shipping or 0),
                        total=float(listing.price) + float(listing.shipping or 0),
                        deal_score=overall,
                        classification=score.get("classification", ""),
                        seller=listing.seller,
                        seller_feedback=int(listing.seller_feedback or 0),
                        seller_positive_pct=float(listing.seller_positive_pct or 0),
                        url=listing.url,
                        estimated_value=score.get("est_fair_value"),
                        vs_median_pct=score.get("vs_median_pct"),
                        scam_warning=score.get("scam_warning"),
                        chat_id=setting.telegram_chat_id,
                    )
                    result["telegram_sent"] += 1
                except Exception:
                    logger.exception("dispatch: telegram send failed (user_id=%s)", setting.user_id)

            # --- ntfy (always instant) ---
            if (
                setting.ntfy_enabled
                and (setting.ntfy_topic or settings.NTFY_TOPIC)
                and overall >= (setting.ntfy_min_score or 0)
            ):
                try:
                    await self.ntfy.send_deal_alert(
                        title=listing.title,
                        price=float(listing.price),
                        shipping=float(listing.shipping or 0),
                        total=float(listing.price) + float(listing.shipping or 0),
                        deal_score=overall,
                        classification=score.get("classification", ""),
                        seller=listing.seller,
                        url=listing.url,
                        estimated_value=score.get("est_fair_value"),
                        vs_median_pct=score.get("vs_median_pct"),
                        scam_warning=score.get("scam_warning"),
                        topic=setting.ntfy_topic or None,
                    )
                    result["ntfy_sent"] += 1
                except Exception:
                    logger.exception("dispatch: ntfy send failed (user_id=%s)", setting.user_id)

            # --- Email (instant or deferred to digest) ---
            if (
                setting.email_enabled
                and setting.email_address
                and overall >= (setting.email_min_score or 0)
            ):
                if setting.email_digest_mode == "instant":
                    try:
                        await self.email.send_deal_alert(
                            to=setting.email_address,
                            title=listing.title,
                            price=float(listing.price),
                            shipping=float(listing.shipping or 0),
                            total=float(listing.price) + float(listing.shipping or 0),
                            deal_score=overall,
                            classification=score.get("classification", ""),
                            seller=listing.seller,
                            url=listing.url,
                            estimated_value=score.get("est_fair_value"),
                            scam_warning=score.get("scam_warning"),
                        )
                        result["email_sent"] += 1
                    except Exception:
                        logger.exception("dispatch: email send failed (user_id=%s)", setting.user_id)
                else:
                    # Daily/weekly digest: the digest job batches these later by
                    # re-querying ListingScores above email_min_score.
                    result["email_deferred"] += 1

        return result


def _aware_to_naive(dt: datetime) -> datetime:
    """Compare timezone-aware DB values against a naive utcnow() safely."""
    return dt.replace(tzinfo=None) if dt.tzinfo is not None else dt
