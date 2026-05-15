# PHASE 05 — Notification System (Telegram + Email)

## Objective
Build the notification delivery system with Telegram Bot API for instant alerts, SMTP email for digests, message templates, and alert dispatch orchestration.

---

## Output Location
`/mnt/agents/output/hardware-deal-tracker/project/backend/app/services/notifications/`

---

## Dependencies
- Phase 1 (database schema) merged to `main`
- Phase 2 (API endpoints) recommended
- Branch from: `main`

---

## Tasks

### Task 1: Telegram Client (`backend/app/services/notifications/telegram.py`)

```python
import httpx
from typing import Optional
from app.core.config import settings

class TelegramClient:
    """Telegram Bot API client for sending deal alerts."""
    
    BASE_URL = "https://api.telegram.org/bot{token}"
    
    def __init__(self, bot_token: Optional[str] = None, chat_id: Optional[str] = None):
        self.token = bot_token or settings.TELEGRAM_BOT_TOKEN
        self.default_chat_id = chat_id or settings.TELEGRAM_CHAT_ID
        self.base_url = self.BASE_URL.format(token=self.token) if self.token else ""
    
    async def send_message(
        self,
        message: str,
        chat_id: Optional[str] = None,
        parse_mode: str = "Markdown",
        disable_web_page_preview: bool = False
    ) -> dict:
        if not self.token:
            return {"ok": False, "error": "Telegram bot token not configured"}
        
        target_chat = chat_id or self.default_chat_id
        if not target_chat:
            return {"ok": False, "error": "No chat ID provided"}
        
        url = f"{self.base_url}/sendMessage"
        payload = {
            "chat_id": target_chat,
            "text": message,
            "parse_mode": parse_mode,
            "disable_web_page_preview": disable_web_page_preview
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            return response.json()
    
    async def send_deal_alert(
        self,
        title: str,
        price: float,
        shipping: float,
        total: float,
        deal_score: int,
        classification: str,
        seller: str,
        seller_feedback: int,
        seller_positive_pct: float,
        url: str,
        image_url: Optional[str] = None,
        estimated_value: Optional[float] = None,
        vs_median_pct: Optional[float] = None,
        lowest_30d: Optional[float] = None,
        chat_id: Optional[str] = None
    ) -> dict:
        # Emoji based on score
        if deal_score >= 85:
            emoji = "🔥"
            label = "HOT DEAL"
        elif deal_score >= 70:
            emoji = "🎯"
            label = "GREAT DEAL"
        elif deal_score >= 50:
            emoji = "✅"
            label = "GOOD DEAL"
        else:
            emoji = "📊"
            label = "FAIR DEAL"
        
        # Build message
        lines = [
            f"{emoji} *{label}* — Score: {deal_score}/100",
            "",
            f"📦 {self._escape_markdown(title)}",
            f"💰 Price: ${price:,.2f}",
        ]
        
        if shipping > 0:
            lines.append(f"🚚 Shipping: ${shipping:,.2f}")
            lines.append(f"💵 Total: ${total:,.2f}")
        
        if estimated_value:
            savings = estimated_value - total
            lines.append(f"📈 Est. Value: ${estimated_value:,.2f}")
            if savings > 0:
                lines.append(f"💸 Potential Savings: ${savings:,.2f}")
        
        if vs_median_pct and vs_median_pct > 0:
            lines.append(f"📉 {vs_median_pct*100:.0f}% below median")
        
        if lowest_30d:
            lines.append(f"📊 30d Low: ${lowest_30d:,.2f}")
        
        lines.extend([
            f"🏪 Seller: {self._escape_markdown(seller)} ({seller_feedback} | {seller_positive_pct:.1f}%)",
            f"🔗 [View on eBay]({url})",
        ])
        
        if image_url:
            lines.append(f"🖼️ [View Image]({image_url})")
        
        lines.append("")
        lines.append("_Hardware Deal Tracker — Self-hosted AI arbitrage agent_")
        
        message = "\n".join(lines)
        return await self.send_message(message, chat_id=chat_id)
    
    def _escape_markdown(self, text: str) -> str:
        """Escape special Markdown characters in Telegram."""
        chars_to_escape = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
        for char in chars_to_escape:
            text = text.replace(char, f'\\{char}')
        return text
```

### Task 2: Email Client (`backend/app/services/notifications/email.py`)

```python
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import Optional, List
from app.core.config import settings

class EmailClient:
    """SMTP email client for sending deal digest emails."""
    
    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        user: Optional[str] = None,
        password: Optional[str] = None
    ):
        self.host = host or settings.SMTP_HOST
        self.port = port or settings.SMTP_PORT
        self.user = user or settings.SMTP_USER
        self.password = password or settings.SMTP_PASSWORD
    
    def is_configured(self) -> bool:
        return bool(self.host and self.user and self.password)
    
    async def send_email(
        self,
        to: str,
        subject: str,
        html_body: str,
        text_body: Optional[str] = None
    ) -> bool:
        if not self.is_configured():
            return False
        
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = self.user
            msg["To"] = to
            
            if text_body:
                msg.attach(MIMEText(text_body, "plain"))
            msg.attach(MIMEText(html_body, "html"))
            
            with smtplib.SMTP(self.host, self.port) as server:
                server.starttls()
                server.login(self.user, self.password)
                server.send_message(msg)
            
            return True
        except Exception as e:
            return False
    
    async def send_deal_alert(
        self,
        to: str,
        title: str,
        price: float,
        shipping: float,
        total: float,
        deal_score: int,
        classification: str,
        seller: str,
        seller_feedback: int,
        seller_positive_pct: float,
        url: str,
        estimated_value: Optional[float] = None,
        vs_median_pct: Optional[float] = None,
    ) -> bool:
        if deal_score >= 85:
            subject_emoji = "🔥"
        elif deal_score >= 70:
            subject_emoji = "🎯"
        else:
            subject_emoji = "📊"
        
        subject = f"{subject_emoji} Deal Alert: {title[:50]} - Score {deal_score}/100"
        
        html = self._build_alert_html(
            title, price, shipping, total, deal_score, classification,
            seller, seller_feedback, seller_positive_pct, url,
            estimated_value, vs_median_pct
        )
        
        return await self.send_email(to, subject, html)
    
    async def send_daily_digest(
        self,
        to: str,
        deals: List[dict],
        date: Optional[datetime] = None
    ) -> bool:
        date = date or datetime.utcnow()
        subject = f"📊 Hardware Deal Tracker Daily Digest — {date.strftime('%Y-%m-%d')}"
        html = self._build_digest_html(deals, date)
        return await self.send_email(to, subject, html)
    
    def _build_alert_html(
        self, title, price, shipping, total, deal_score, classification,
        seller, seller_feedback, seller_positive_pct, url,
        estimated_value, vs_median_pct
    ) -> str:
        score_color = self._score_color(deal_score)
        
        savings_html = ""
        if estimated_value:
            savings = estimated_value - total
            savings_pct = (savings / estimated_value * 100) if estimated_value > 0 else 0
            savings_html = f'<p><strong>Potential Savings:</strong> ${savings:,.2f} ({savings_pct:.0f}%)</p>'
        
        vs_median_html = ""
        if vs_median_pct and vs_median_pct > 0:
            vs_median_html = f'<p><strong>vs Median:</strong> {vs_median_pct*100:.0f}% below</p>'
        
        return f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; color: white; border-radius: 8px 8px 0 0;">
                <h2 style="margin: 0;">Hardware Deal Tracker</h2>
                <p style="margin: 5px 0 0 0; opacity: 0.9;">AI-Powered Enterprise Hardware Arbitrage</p>
            </div>
            <div style="padding: 20px; border: 1px solid #e0e0e0; border-top: none;">
                <div style="background: {score_color}; color: white; display: inline-block; padding: 8px 16px; border-radius: 20px; font-weight: bold; margin-bottom: 15px;">
                    Score: {deal_score}/100 — {classification.upper().replace('_', ' ')}
                </div>
                <h3 style="color: #333; margin-top: 0;">{title}</h3>
                <p><strong>Price:</strong> ${price:,.2f}</p>
                <p><strong>Shipping:</strong> ${shipping:,.2f}</p>
                <p><strong>Total:</strong> ${total:,.2f}</p>
                {savings_html}
                {vs_median_html}
                <p><strong>Seller:</strong> {seller} ({seller_feedback} feedback | {seller_positive_pct:.1f}% positive)</p>
                <a href="{url}" style="display: inline-block; background: #667eea; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; margin-top: 10px;">View on eBay</a>
            </div>
            <div style="padding: 15px; text-align: center; color: #888; font-size: 12px; border: 1px solid #e0e0e0; border-top: none; border-radius: 0 0 8px 8px;">
                Hardware Deal Tracker — Self-hosted AI arbitrage agent
            </div>
        </body>
        </html>
        """
    
    def _build_digest_html(self, deals: List[dict], date: datetime) -> str:
        deal_rows = ""
        for deal in deals:
            color = self._score_color(deal.get("score", 50))
            deal_rows += f"""
            <tr style="border-bottom: 1px solid #e0e0e0;">
                <td style="padding: 12px;"><span style="background: {color}; color: white; padding: 4px 10px; border-radius: 12px; font-size: 12px; font-weight: bold;">{deal.get('score', 0)}</span></td>
                <td style="padding: 12px; font-size: 14px;">{deal.get('title', 'Unknown')[:60]}</td>
                <td style="padding: 12px; font-weight: bold;">${deal.get('total_price', 0):,.2f}</td>
                <td style="padding: 12px;"><a href="{deal.get('url', '#')}" style="color: #667eea;">View</a></td>
            </tr>
            """
        
        return f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 700px; margin: 0 auto;">
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; color: white; border-radius: 8px 8px 0 0;">
                <h2 style="margin: 0;">📊 Daily Deal Digest</h2>
                <p style="margin: 5px 0 0 0; opacity: 0.9;">{date.strftime('%A, %B %d, %Y')}</p>
            </div>
            <div style="padding: 20px; border: 1px solid #e0e0e0; border-top: none;">
                <p><strong>{len(deals)} deals</strong> found today</p>
                <table style="width: 100%; border-collapse: collapse; margin-top: 15px;">
                    <thead>
                        <tr style="background: #f5f5f5; text-align: left;">
                            <th style="padding: 12px;">Score</th>
                            <th style="padding: 12px;">Item</th>
                            <th style="padding: 12px;">Total</th>
                            <th style="padding: 12px;">Link</th>
                        </tr>
                    </thead>
                    <tbody>{deal_rows}</tbody>
                </table>
            </div>
        </body>
        </html>
        """
    
    def _score_color(self, score: int) -> str:
        if score >= 85:
            return "#e74c3c"  # Red (hot)
        elif score >= 70:
            return "#f39c12"  # Orange (great)
        elif score >= 50:
            return "#27ae60"  # Green (good)
        else:
            return "#95a5a6"  # Gray (fair)
```

### Task 3: Alert Dispatcher (`backend/app/services/notifications/dispatcher.py`)

```python
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from app.core.config import settings
from app.models.alert import Alert
from app.models.listing import Listing
from app.models.listing_score import ListingScore
from app.models.notification_setting import NotificationSetting
from app.services.notifications.telegram import TelegramClient
from app.services.notifications.email import EmailClient

class AlertDispatcher:
    """Routes alerts to appropriate notification channels."""
    
    def __init__(self):
        self.telegram = TelegramClient()
        self.email = EmailClient()
    
    async def dispatch(
        self,
        db: AsyncSession,
        listing_id: int,
        score_id: int,
        user_id: Optional[int] = None
    ) -> dict:
        """Dispatch alert for a scored listing."""
        # Get listing and score
        listing_result = await db.execute(select(Listing).where(Listing.id == listing_id))
        listing = listing_result.scalar_one_or_none()
        if not listing:
            return {"error": "Listing not found"}
        
        score_result = await db.execute(select(ListingScore).where(ListingScore.id == score_id))
        score = score_result.scalar_one_or_none()
        if not score:
            return {"error": "Score not found"}
        
        total_price = float(listing.price) + float(listing.shipping)
        
        # Get user notification settings
        settings_result = await db.execute(
            select(NotificationSetting).where(NotificationSetting.user_id == (user_id or 1))
        )
        notif_settings = settings_result.scalar_one_or_none()
        if not notif_settings:
            return {"error": "No notification settings found"}
        
        results = {"telegram": None, "email": None}
        
        # Telegram alert
        if notif_settings.telegram_enabled and notif_settings.telegram_chat_id:
            if score.overall_score >= notif_settings.telegram_min_score:
                if not self._is_muted(notif_settings):
                    try:
                        tg_result = await self.telegram.send_deal_alert(
                            title=listing.title,
                            price=float(listing.price),
                            shipping=float(listing.shipping),
                            total=total_price,
                            deal_score=score.overall_score,
                            classification=score.classification,
                            seller=listing.seller,
                            seller_feedback=listing.seller_feedback,
                            seller_positive_pct=float(listing.seller_positive_pct),
                            url=listing.url,
                            image_url=listing.image_url,
                            estimated_value=float(score.est_fair_value) if score.est_fair_value else None,
                            vs_median_pct=float(score.vs_median_pct) if score.vs_median_pct else None,
                            chat_id=notif_settings.telegram_chat_id
                        )
                        results["telegram"] = tg_result
                    except Exception as e:
                        results["telegram"] = {"ok": False, "error": str(e)}
                else:
                    results["telegram"] = {"ok": False, "muted": True}
        
        # Email alert
        if notif_settings.email_enabled and notif_settings.email_address:
            if score.overall_score >= notif_settings.email_min_score:
                if notif_settings.email_digest_mode == "instant":
                    try:
                        sent = await self.email.send_deal_alert(
                            to=notif_settings.email_address,
                            title=listing.title,
                            price=float(listing.price),
                            shipping=float(listing.shipping),
                            total=total_price,
                            deal_score=score.overall_score,
                            classification=score.classification,
                            seller=listing.seller,
                            seller_feedback=listing.seller_feedback,
                            seller_positive_pct=float(listing.seller_positive_pct),
                            url=listing.url,
                            estimated_value=float(score.est_fair_value) if score.est_fair_value else None,
                            vs_median_pct=float(score.vs_median_pct) if score.vs_median_pct else None,
                        )
                        results["email"] = {"sent": sent}
                    except Exception as e:
                        results["email"] = {"sent": False, "error": str(e)}
                # hourly/daily handled by n8n workflows
        
        # Record alerts
        for channel, result in results.items():
            was_sent = False
            if isinstance(result, dict):
                was_sent = result.get("ok", False) or result.get("sent", False)
            
            alert = Alert(
                listing_id=listing_id,
                tracked_item_id=listing.tracked_item_id,
                score_id=score_id,
                channel=channel,
                alert_type="instant" if channel == "telegram" else (notif_settings.email_digest_mode if channel == "email" else "instant"),
                was_sent=was_sent,
                sent_at=datetime.utcnow() if was_sent else None
            )
            db.add(alert)
        
        await db.flush()
        return results
    
    def _is_muted(self, notif_settings: NotificationSetting) -> bool:
        if notif_settings.mute_until and notif_settings.mute_until > datetime.utcnow():
            return True
        return False
```

### Task 4: API Endpoints for Notifications

**`backend/app/api/v1/endpoints/alerts.py`** — Replace stub:

```python
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional
from app.api.deps import get_db, get_current_user
from app.models.alert import Alert
from app.models.notification_setting import NotificationSetting
from app.schemas.alert import AlertResponse, AlertListResponse
from app.services.notifications.dispatcher import AlertDispatcher

router = APIRouter(prefix="/alerts", tags=["alerts"])

@router.get("")
async def list_alerts(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    channel: Optional[str] = None,
    sent: Optional[bool] = None,
    db: AsyncSession = Depends(get_db),
    user = Depends(get_current_user)
):
    query = select(Alert)
    if channel:
        query = query.where(Alert.channel == channel)
    if sent is not None:
        query = query.where(Alert.was_sent == sent)
    
    count_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = count_result.scalar()
    
    query = query.offset((page - 1) * per_page).limit(per_page).order_by(Alert.created_at.desc())
    result = await db.execute(query)
    alerts = result.scalars().all()
    
    return {"alerts": alerts, "total": total, "page": page, "per_page": per_page}

@router.post("/dispatch/{listing_id}")
async def dispatch_alert(
    listing_id: int,
    score_id: int,
    db: AsyncSession = Depends(get_db),
    user = Depends(get_current_user)
):
    dispatcher = AlertDispatcher()
    return await dispatcher.dispatch(db, listing_id, score_id, user.id)
```

### Task 5: Tests

**`backend/tests/test_notifications.py`**:
```python
import pytest
from app.services.notifications.telegram import TelegramClient
from app.services.notifications.email import EmailClient
from app.services.notifications.dispatcher import AlertDispatcher

@pytest.fixture
def telegram_client():
    return TelegramClient(bot_token="test_token", chat_id="123456")

def test_telegram_markdown_escape(telegram_client):
    escaped = telegram_client._escape_markdown("Test_underscore [link]")
    assert "\\_" in escaped
    assert "\\[" in escaped

def test_score_color():
    client = EmailClient()
    assert client._score_color(90) == "#e74c3c"
    assert client._score_color(75) == "#f39c12"
    assert client._score_color(60) == "#27ae60"
    assert client._score_color(30) == "#95a5a6"

def test_email_client_not_configured():
    client = EmailClient(host="", port=0, user="", password="")
    assert not client.is_configured()
```

---

## Deliverables

- [ ] `app/services/notifications/telegram.py` — Telegram Bot API client
- [ ] `app/services/notifications/email.py` — SMTP email client
- [ ] `app/services/notifications/dispatcher.py` — Alert routing
- [ ] `app/services/notifications/__init__.py` — Exports
- [ ] `app/api/v1/endpoints/alerts.py` — Updated with dispatch endpoint
- [ ] `tests/test_notifications.py` — Notification tests

## Git
Branch: `phase-05-notifications`
Base: `main` (after Phase 1 merge)
Commit message: `feat(phase-5): Telegram + email notifications, alert dispatcher`
