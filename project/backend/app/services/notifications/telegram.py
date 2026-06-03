
import httpx

from app.core.config import settings


class TelegramClient:
    """Telegram Bot API client for sending deal alerts."""

    BASE_URL = "https://api.telegram.org/bot{token}"

    def __init__(self, bot_token: str | None = None, chat_id: str | None = None):
        self.token = bot_token or settings.TELEGRAM_BOT_TOKEN
        self.default_chat_id = chat_id or settings.TELEGRAM_CHAT_ID
        self.base_url = self.BASE_URL.format(token=self.token) if self.token else ""

    async def send_message(self, message: str, chat_id: str | None = None, parse_mode: str = "Markdown") -> dict:
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
            "disable_web_page_preview": False
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            return response.json()

    async def send_deal_alert(self, title: str, price: float, shipping: float, total: float,
                              deal_score: int, classification: str, seller: str,
                              seller_feedback: int, seller_positive_pct: float, url: str,
                              estimated_value: float | None = None,
                              vs_median_pct: float | None = None,
                              scam_warning: str | None = None,
                              chat_id: str | None = None) -> dict:
        if deal_score >= 85:
            emoji, label = "🔥", "HOT DEAL"
        elif deal_score >= 70:
            emoji, label = "🎯", "GREAT DEAL"
        elif deal_score >= 50:
            emoji, label = "✅", "GOOD DEAL"
        else:
            emoji, label = "📊", "FAIR DEAL"

        if classification == "suspicious":
            emoji, label = "⚠️", "SUSPICIOUS"

        lines = [f"{emoji} *{label}* — Score: {deal_score}/100", "", f"📦 {self._escape(title)}"]
        lines.append(f"💰 Price: ${price:,.2f}")
        if shipping > 0:
            lines.append(f"🚚 Shipping: ${shipping:,.2f}")
            lines.append(f"💵 Total: ${total:,.2f}")
        if estimated_value:
            lines.append(f"📈 Est. Value: ${estimated_value:,.2f}")
        if vs_median_pct and vs_median_pct > 0:
            lines.append(f"📉 {vs_median_pct * 100:.0f}% below median")
        if scam_warning:
            lines.append(f"🚨 *{self._escape(scam_warning)}*")
        lines.append(f"🏪 Seller: {self._escape(seller)} ({seller_feedback} | {seller_positive_pct:.1f}%)")
        lines.append(f"🔗 [View on eBay]({url})")
        lines.append("")
        lines.append("_Hardware Deal Tracker_")

        return await self.send_message("\n".join(lines), chat_id=chat_id)

    def _escape(self, text: str) -> str:
        for char in ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']:
            text = text.replace(char, f'\\{char}')
        return text
