import httpx

from app.core.config import settings


class NtfyClient:
    """ntfy (self-hosted push) client for sending deal alerts.

    Mirrors TelegramClient. Publishes to ``{base_url}/{topic}``. The homelab ntfy
    requires auth — a Bearer token (NTFY_TOKEN) takes precedence, else HTTP basic
    (NTFY_USERNAME/NTFY_PASSWORD). ntfy headers must be ASCII, so the Title is kept
    plain; emoji/unicode go in the UTF-8 body and via the Tags header.
    """

    def __init__(
        self,
        base_url: str | None = None,
        topic: str | None = None,
        token: str | None = None,
        username: str | None = None,
        password: str | None = None,
    ):
        self.base_url = (base_url or settings.NTFY_BASE_URL).rstrip("/")
        self.default_topic = topic or settings.NTFY_TOPIC
        self.token = token or settings.NTFY_TOKEN
        self.username = username if username is not None else settings.NTFY_USERNAME
        self.password = password if password is not None else settings.NTFY_PASSWORD

    def _auth(self) -> tuple[str, str] | None:
        # Bearer token (set as a header) wins; otherwise fall back to basic auth.
        if self.token:
            return None
        if self.username and self.password:
            return (self.username, self.password)
        return None

    async def send_message(
        self,
        message: str,
        topic: str | None = None,
        title: str | None = None,
        priority: int | None = None,
        tags: list[str] | None = None,
        click: str | None = None,
        markdown: bool = False,
    ) -> dict:
        if not self.base_url:
            return {"ok": False, "error": "ntfy base URL not configured"}
        target = topic or self.default_topic
        if not target:
            return {"ok": False, "error": "No ntfy topic provided"}

        headers: dict[str, str] = {}
        if title:
            headers["Title"] = title.encode("ascii", "ignore").decode().strip() or "Deal Tracker"
        if priority:
            headers["Priority"] = str(priority)
        if tags:
            headers["Tags"] = ",".join(tags)
        if click:
            headers["Click"] = click
        if markdown:
            headers["Markdown"] = "yes"
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"

        url = f"{self.base_url}/{target}"
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                url, content=message.encode("utf-8"), headers=headers, auth=self._auth()
            )
            response.raise_for_status()
            return {"ok": True, "response": response.json() if response.content else {}}

    async def send_deal_alert(
        self,
        title: str,
        price: float,
        shipping: float,
        total: float,
        deal_score: int,
        classification: str,
        seller: str,
        url: str,
        estimated_value: float | None = None,
        vs_median_pct: float | None = None,
        scam_warning: str | None = None,
        topic: str | None = None,
    ) -> dict:
        if deal_score >= 85:
            label, priority, tag = "HOT DEAL", 5, "fire"
        elif deal_score >= 70:
            label, priority, tag = "GREAT DEAL", 4, "dart"
        elif deal_score >= 50:
            label, priority, tag = "GOOD DEAL", 3, "white_check_mark"
        else:
            label, priority, tag = "FAIR DEAL", 3, "bar_chart"

        if classification == "suspicious":
            label, priority, tag = "SUSPICIOUS", 4, "warning"

        # Plain hyphen (not em-dash) so the ASCII-only Title header stays clean.
        ntitle = f"{label} - Score {deal_score}/100"

        lines = [title, f"💰 Price: ${price:,.2f}"]
        if shipping > 0:
            lines.append(f"💵 Total: ${total:,.2f}")
        if estimated_value:
            lines.append(f"📈 Est. value: ${estimated_value:,.2f}")
        if vs_median_pct and vs_median_pct > 0:
            lines.append(f"📉 {vs_median_pct * 100:.0f}% below median")
        if scam_warning:
            lines.append(f"🚨 {scam_warning}")
        lines.append(f"🏪 Seller: {seller}")

        return await self.send_message(
            "\n".join(lines), topic=topic, title=ntitle,
            priority=priority, tags=[tag], click=url,
        )
