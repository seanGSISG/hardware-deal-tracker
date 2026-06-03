import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import aiosmtplib

from app.core.config import settings

logger = logging.getLogger(__name__)


class EmailClient:
    """Async SMTP email client (aiosmtplib) for deal alerts and digests.

    Migrated off blocking ``smtplib`` so sends never stall the event loop /
    scheduler (T2.3/digest). All public sends are best-effort and return a bool.
    """

    def __init__(self, host: str | None = None, port: int | None = None,
                 user: str | None = None, password: str | None = None,
                 from_addr: str | None = None):
        self.host = host or settings.SMTP_HOST
        self.port = port or settings.SMTP_PORT
        self.user = user or settings.SMTP_USER
        self.password = password or settings.SMTP_PASSWORD
        # SMTP_FROM overrides the envelope From; defaults to the auth user.
        self.from_addr = from_addr or settings.SMTP_FROM or self.user

    def is_configured(self) -> bool:
        return bool(self.host and self.user and self.password)

    async def send_email(self, to: str, subject: str, html_body: str, text_body: str | None = None) -> bool:
        if not self.is_configured():
            return False
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = self.from_addr
            msg["To"] = to
            if text_body:
                msg.attach(MIMEText(text_body, "plain"))
            msg.attach(MIMEText(html_body, "html"))

            await aiosmtplib.send(
                msg,
                hostname=self.host,
                port=self.port,
                username=self.user,
                password=self.password,
                start_tls=True,
            )
            return True
        except Exception:
            logger.exception("email send failed (to=%s)", to)
            return False

    async def send_deal_alert(self, to: str, title: str, price: float, shipping: float,
                              total: float, deal_score: int, classification: str,
                              seller: str, url: str, estimated_value: float | None = None,
                              scam_warning: str | None = None) -> bool:
        emoji = "🔥" if deal_score >= 85 else "🎯" if deal_score >= 70 else "📊"
        if classification == "suspicious":
            emoji = "⚠️"
        subject = f"{emoji} Deal Alert: {title[:50]} - Score {deal_score}/100"

        color = "#e74c3c" if deal_score >= 85 else "#f39c12" if deal_score >= 70 else "#27ae60" if deal_score >= 50 else "#95a5a6"
        scam_html = f'<p style="color:#e74c3c;font-weight:bold">⚠️ {scam_warning}</p>' if scam_warning else ""

        html = f"""
        <html><body style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;">
        <div style="background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);padding:20px;color:white;border-radius:8px 8px 0 0;">
            <h2 style="margin:0">Hardware Deal Tracker</h2></div>
        <div style="padding:20px;border:1px solid #e0e0e0;border-top:none;">
            <div style="background:{color};color:white;display:inline-block;padding:8px 16px;border-radius:20px;font-weight:bold;margin-bottom:15px;">
                Score: {deal_score}/100 — {classification.upper().replace('_',' ')}
            </div>
            {scam_html}
            <h3 style="color:#333;margin-top:0">{title}</h3>
            <p><strong>Price:</strong> ${price:,.2f}</p>
            <p><strong>Total:</strong> ${total:,.2f}</p>
            {f'<p><strong>Est. Value:</strong> ${estimated_value:,.2f}</p>' if estimated_value else ''}
            <p><strong>Seller:</strong> {seller}</p>
            <a href="{url}" style="display:inline-block;background:#667eea;color:white;padding:12px 24px;text-decoration:none;border-radius:6px;margin-top:10px;">View on eBay</a>
        </div></body></html>
        """
        return await self.send_email(to, subject, html)

    async def send_deal_digest(self, to: str, deals: list[dict]) -> bool:
        """Batch many deals into a single digest email.

        ``deals`` is a list of dicts with at least ``title``, ``total``,
        ``overall_score``, ``classification`` and ``url`` (``est_fair_value``
        optional). Returns False (without sending) when there's nothing to send.
        """
        if not deals:
            return False

        count = len(deals)
        subject = f"📬 Deal Digest — {count} new deal{'s' if count != 1 else ''}"

        rows = []
        for d in deals:
            score = int(d.get("overall_score", 0))
            color = "#e74c3c" if score >= 85 else "#f39c12" if score >= 70 else "#27ae60" if score >= 50 else "#95a5a6"
            est = d.get("est_fair_value")
            est_html = f'<span style="color:#888"> · est ${est:,.0f}</span>' if est else ""
            classification = str(d.get("classification", "")).upper().replace("_", " ")
            rows.append(
                f'<tr><td style="padding:10px;border-bottom:1px solid #eee;">'
                f'<span style="background:{color};color:white;padding:2px 8px;border-radius:10px;font-size:12px;font-weight:bold;">{score}</span> '
                f'<a href="{d.get("url", "#")}" style="color:#333;text-decoration:none;font-weight:bold;">{d.get("title", "")}</a> '
                f'<span style="color:#888;font-size:12px;">— {classification}</span>'
                f'<br><span style="color:#555;">${float(d.get("total", 0)):,.2f}</span>{est_html}'
                f'</td></tr>'
            )

        html = f"""
        <html><body style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;">
        <div style="background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);padding:20px;color:white;border-radius:8px 8px 0 0;">
            <h2 style="margin:0">Hardware Deal Tracker — Digest</h2>
            <p style="margin:4px 0 0;opacity:0.9;">{count} new deal{'s' if count != 1 else ''}</p>
        </div>
        <div style="padding:0 20px 20px;border:1px solid #e0e0e0;border-top:none;">
            <table style="width:100%;border-collapse:collapse;">{''.join(rows)}</table>
        </div></body></html>
        """
        return await self.send_email(to, subject, html)
