"""Unit tests for the email + telegram transports (mocking the wire)."""
import app.services.notifications.email as email_mod
from app.services.notifications.email import EmailClient
from app.services.notifications.telegram import TelegramClient

# --- Email -------------------------------------------------------------------

def _email_client() -> EmailClient:
    return EmailClient(host="smtp.test", port=587, user="bot@test", password="pw")


async def test_send_email_uses_aiosmtplib_not_blocking_smtplib(monkeypatch):
    """story-digest: sends must go through aiosmtplib (non-blocking), not smtplib."""
    sent = {}

    async def _fake_send(message, hostname=None, port=None, username=None,
                         password=None, start_tls=None, **kwargs):
        sent["hostname"] = hostname
        sent["port"] = port
        sent["to"] = message["To"]
        sent["subject"] = message["Subject"]
        return {}

    monkeypatch.setattr(email_mod.aiosmtplib, "send", _fake_send)

    client = _email_client()
    ok = await client.send_email("you@test", "Subject", "<b>hi</b>")
    assert ok is True
    assert sent["hostname"] == "smtp.test"
    assert sent["to"] == "you@test"
    assert sent["subject"] == "Subject"


async def test_send_email_returns_false_when_unconfigured():
    client = EmailClient(host="", user="", password="")
    assert await client.send_email("you@test", "S", "B") is False


async def test_send_email_swallows_transport_errors(monkeypatch):
    async def _boom(*a, **k):
        raise RuntimeError("smtp down")

    monkeypatch.setattr(email_mod.aiosmtplib, "send", _boom)
    client = _email_client()
    assert await client.send_email("you@test", "S", "B") is False


async def test_send_deal_digest_batches_into_one_email(monkeypatch):
    captured = {}

    async def _fake_send(message, **kwargs):
        captured["to"] = message["To"]
        captured["subject"] = message["Subject"]
        # Grab the HTML part payload.
        captured["body"] = message.get_payload()[-1].get_payload(decode=True).decode()
        return {}

    monkeypatch.setattr(email_mod.aiosmtplib, "send", _fake_send)

    deals = [
        {"title": "EPYC 7F72", "total": 200.0, "overall_score": 88,
         "classification": "hot_deal", "url": "https://ebay.com/itm/1", "est_fair_value": 350.0},
        {"title": "RTX 6000 Ada", "total": 4000.0, "overall_score": 72,
         "classification": "great_deal", "url": "https://ebay.com/itm/2", "est_fair_value": 4800.0},
    ]
    client = _email_client()
    ok = await client.send_deal_digest("you@test", deals)
    assert ok is True
    assert captured["to"] == "you@test"
    assert "EPYC 7F72" in captured["body"]
    assert "RTX 6000 Ada" in captured["body"]
    assert "2" in captured["subject"]  # deal count in subject


async def test_send_deal_digest_empty_sends_nothing(monkeypatch):
    called = {"n": 0}

    async def _fake_send(message, **kwargs):
        called["n"] += 1
        return {}

    monkeypatch.setattr(email_mod.aiosmtplib, "send", _fake_send)
    client = _email_client()
    assert await client.send_deal_digest("you@test", []) is False
    assert called["n"] == 0


# --- Telegram ----------------------------------------------------------------

class _FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


class _FakeAsyncClient:
    sent = []

    def __init__(self, *a, **k):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False

    async def post(self, url, json=None):
        _FakeAsyncClient.sent.append({"url": url, "json": json})
        return _FakeResponse({"ok": True, "result": {"message_id": 7}})


async def test_telegram_send_message_posts_to_api(monkeypatch):
    import app.services.notifications.telegram as tg_mod

    _FakeAsyncClient.sent = []
    monkeypatch.setattr(tg_mod.httpx, "AsyncClient", _FakeAsyncClient)

    client = TelegramClient(bot_token="abc", chat_id="999")
    res = await client.send_message("hello")
    assert res["ok"] is True
    assert _FakeAsyncClient.sent[0]["json"]["chat_id"] == "999"
    assert _FakeAsyncClient.sent[0]["json"]["text"] == "hello"


async def test_telegram_no_token_returns_error_without_network():
    client = TelegramClient(bot_token="", chat_id="999")
    res = await client.send_message("hello")
    assert res["ok"] is False


async def test_telegram_deal_alert_formats_and_sends(monkeypatch):
    import app.services.notifications.telegram as tg_mod

    _FakeAsyncClient.sent = []
    monkeypatch.setattr(tg_mod.httpx, "AsyncClient", _FakeAsyncClient)

    client = TelegramClient(bot_token="abc", chat_id="999")
    res = await client.send_deal_alert(
        title="EPYC 7F72", price=200.0, shipping=0.0, total=200.0,
        deal_score=88, classification="hot_deal", seller="seller",
        seller_feedback=500, seller_positive_pct=99.0, url="https://ebay.com/itm/1",
    )
    assert res["ok"] is True
    text = _FakeAsyncClient.sent[0]["json"]["text"]
    assert "HOT DEAL" in text
    assert "200" in text


# --- ntfy --------------------------------------------------------------------

import app.services.notifications.ntfy as ntfy_mod  # noqa: E402
from app.services.notifications.ntfy import NtfyClient  # noqa: E402


class _FakeNtfyResp:
    content = b'{"id":"abc"}'

    def raise_for_status(self):
        return None

    def json(self):
        return {"id": "abc"}


class _FakeNtfyAsyncClient:
    captured: dict = {}

    def __init__(self, *a, **k):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, *a):
        return False

    async def post(self, url, content=None, headers=None, auth=None):
        _FakeNtfyAsyncClient.captured = {
            "url": url, "content": content, "headers": headers or {}, "auth": auth,
        }
        return _FakeNtfyResp()


async def test_ntfy_send_message_builds_request_with_basic_auth(monkeypatch):
    monkeypatch.setattr(ntfy_mod.httpx, "AsyncClient", _FakeNtfyAsyncClient)
    client = NtfyClient(base_url="https://ntfy.test/", topic="deals", username="u", password="p")
    res = await client.send_message("hello", title="Deal", priority=4, tags=["fire"], click="https://x")
    assert res["ok"] is True
    cap = _FakeNtfyAsyncClient.captured
    assert cap["url"] == "https://ntfy.test/deals"
    assert cap["content"] == b"hello"
    assert cap["headers"]["Title"] == "Deal"
    assert cap["headers"]["Priority"] == "4"
    assert cap["headers"]["Tags"] == "fire"
    assert cap["headers"]["Click"] == "https://x"
    assert cap["auth"] == ("u", "p")


async def test_ntfy_bearer_token_takes_precedence_over_basic(monkeypatch):
    monkeypatch.setattr(ntfy_mod.httpx, "AsyncClient", _FakeNtfyAsyncClient)
    client = NtfyClient(base_url="https://ntfy.test", topic="deals", token="tok_abc",
                        username="u", password="p")
    await client.send_message("hi")
    cap = _FakeNtfyAsyncClient.captured
    assert cap["headers"]["Authorization"] == "Bearer tok_abc"
    assert cap["auth"] is None


async def test_ntfy_returns_error_when_unconfigured():
    assert (await NtfyClient(base_url="", topic="").send_message("hi"))["ok"] is False
    assert (await NtfyClient(base_url="https://ntfy.test", topic="").send_message("hi"))["ok"] is False


async def test_ntfy_title_is_ascii_sanitised(monkeypatch):
    monkeypatch.setattr(ntfy_mod.httpx, "AsyncClient", _FakeNtfyAsyncClient)
    client = NtfyClient(base_url="https://ntfy.test", topic="deals", username="u", password="p")
    await client.send_message("body", title="HOT 🔥 DEAL")
    # Non-ASCII stripped from the header (ntfy headers must be ASCII).
    assert _FakeNtfyAsyncClient.captured["headers"]["Title"].isascii()
