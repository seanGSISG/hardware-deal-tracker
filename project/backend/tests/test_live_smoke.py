"""Creds-gated live-smoke tests (story-005 / feature-004).

These hit REAL external services (OpenRouter, a local vLLM server, Telegram, SMTP)
and are marked `live_smoke` + `skipif`-gated on the relevant creds being present, so
they SKIP cleanly by default and CI (which runs `-m "not real_ebay and not
live_smoke"`) never needs live creds. Each live test records the returned
message/response id into the log so the round-trip is auditable in the journal.

The gating behavior itself is unit-tested (no creds -> the live tests are collected
as SKIPPED, never failed/errored).
"""
import logging
import os

import pytest

logger = logging.getLogger("live_smoke")


def _openrouter_ready() -> bool:
    return bool(os.getenv("OPENROUTER_API_KEY"))


def _vllm_ready() -> bool:
    return os.getenv("AI_PROVIDER") == "vllm" and bool(os.getenv("AI_VLLM_BASE_URL"))


def _telegram_ready() -> bool:
    return bool(os.getenv("TELEGRAM_BOT_TOKEN")) and bool(os.getenv("TELEGRAM_CHAT_ID"))


def _smtp_ready() -> bool:
    return (
        bool(os.getenv("SMTP_HOST"))
        and bool(os.getenv("SMTP_USER"))
        and bool(os.getenv("SMTP_PASSWORD"))
        and bool(os.getenv("LIVE_SMOKE_EMAIL_TO"))
    )


# --------------------------------------------------------------------------- #
# Gating behavior (always runs — no live creds required).
# Proves the live tests are correctly skipped when creds are absent.
# --------------------------------------------------------------------------- #
def test_live_smoke_marker_is_registered(pytestconfig):
    markers = pytestconfig.getini("markers")
    assert any(m.startswith("live_smoke:") for m in markers), (
        "live_smoke marker must be registered in pyproject.toml"
    )


def test_readiness_gates_skip_without_creds(monkeypatch):
    # With the relevant env cleared, every readiness gate must report not-ready,
    # which is what drives the skipif on the live tests below.
    for var in (
        "OPENROUTER_API_KEY",
        "AI_PROVIDER",
        "AI_VLLM_BASE_URL",
        "TELEGRAM_BOT_TOKEN",
        "TELEGRAM_CHAT_ID",
        "SMTP_HOST",
        "SMTP_USER",
        "SMTP_PASSWORD",
        "LIVE_SMOKE_EMAIL_TO",
    ):
        monkeypatch.delenv(var, raising=False)
    assert _openrouter_ready() is False
    assert _vllm_ready() is False
    assert _telegram_ready() is False
    assert _smtp_ready() is False


# --------------------------------------------------------------------------- #
# Live round-trips (skipped unless creds are present).
# --------------------------------------------------------------------------- #
@pytest.mark.live_smoke
@pytest.mark.skipif(not _openrouter_ready(), reason="OPENROUTER_API_KEY not set")
async def test_openrouter_completion_round_trip(caplog):
    from app.services.ai.client import AIClient

    client = AIClient()
    assert client.is_enabled, "AI client must be enabled with OpenRouter creds set"
    with caplog.at_level(logging.INFO, logger="live_smoke"):
        content = await client.complete(
            [{"role": "user", "content": "Reply with the single word: pong"}],
            max_tokens=8,
        )
    assert content is not None
    logger.info("openrouter round-trip ok: response=%r", content.strip())
    assert "openrouter round-trip ok" in caplog.text


@pytest.mark.live_smoke
@pytest.mark.skipif(not _vllm_ready(), reason="AI_PROVIDER!=vllm or AI_VLLM_BASE_URL not set")
async def test_vllm_completion_round_trip(caplog):
    from app.services.ai.client import AIClient

    client = AIClient()
    assert client.is_enabled, "AI client must be enabled with vLLM configured"
    with caplog.at_level(logging.INFO, logger="live_smoke"):
        content = await client.complete(
            [{"role": "user", "content": "Reply with the single word: pong"}],
            max_tokens=8,
        )
    assert content is not None
    logger.info("vllm round-trip ok: response=%r", content.strip())
    assert "vllm round-trip ok" in caplog.text


@pytest.mark.live_smoke
@pytest.mark.skipif(not _telegram_ready(), reason="Telegram creds not set")
async def test_telegram_send(caplog):
    from app.services.notifications.telegram import TelegramClient

    client = TelegramClient()
    with caplog.at_level(logging.INFO, logger="live_smoke"):
        result = await client.send_message("Hardware Deal Tracker live-smoke ping")
        assert result.get("ok") is True, result
        message_id = result["result"]["message_id"]
        logger.info("telegram send ok: message_id=%s", message_id)
    assert "telegram send ok: message_id=" in caplog.text


@pytest.mark.live_smoke
@pytest.mark.skipif(not _smtp_ready(), reason="SMTP creds / LIVE_SMOKE_EMAIL_TO not set")
async def test_smtp_send(caplog):
    from app.services.notifications.email import EmailClient

    client = EmailClient()
    assert client.is_configured()
    to = os.environ["LIVE_SMOKE_EMAIL_TO"]
    with caplog.at_level(logging.INFO, logger="live_smoke"):
        ok = await client.send_email(
            to=to,
            subject="HDT live-smoke",
            html_body="<p>Hardware Deal Tracker live-smoke ping</p>",
            text_body="Hardware Deal Tracker live-smoke ping",
        )
        assert ok is True
        logger.info("smtp send ok: accepted recipient=%s host=%s", to, client.host)
    assert "smtp send ok:" in caplog.text
