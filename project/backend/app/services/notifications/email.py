import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import Optional, List
from app.core.config import settings


class EmailClient:
    """SMTP email client for sending deal digest emails."""

    def __init__(self, host: Optional[str] = None, port: Optional[int] = None,
                 user: Optional[str] = None, password: Optional[str] = None):
        self.host = host or settings.SMTP_HOST
        self.port = port or settings.SMTP_PORT
        self.user = user or settings.SMTP_USER
        self.password = password or settings.SMTP_PASSWORD

    def is_configured(self) -> bool:
        return bool(self.host and self.user and self.password)

    async def send_email(self, to: str, subject: str, html_body: str, text_body: Optional[str] = None) -> bool:
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
        except Exception:
            return False

    async def send_deal_alert(self, to: str, title: str, price: float, shipping: float,
                              total: float, deal_score: int, classification: str,
                              seller: str, url: str, estimated_value: Optional[float] = None,
                              scam_warning: Optional[str] = None) -> bool:
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
