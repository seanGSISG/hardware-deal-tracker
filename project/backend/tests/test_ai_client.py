"""story-3 (feature-006): configurable AI provider abstraction (OpenRouter | vLLM)."""
import httpx

from app.core.config import settings
from app.services.ai.client import AIClient


def _chat_response(content: str):
    class _Resp:
        def raise_for_status(self):
            pass

        def json(self):
            return {"choices": [{"message": {"content": content}}]}

    return _Resp()


def test_ai_disabled_by_default():
    # AI must be opt-in; with AI_ENABLED False the client is inert.
    assert settings.AI_ENABLED is False
    assert AIClient().is_enabled is False


async def test_disabled_client_returns_none(monkeypatch):
    monkeypatch.setattr(settings, "AI_ENABLED", False)
    out = await AIClient().complete([{"role": "user", "content": "hi"}])
    assert out is None


async def test_openrouter_completion(monkeypatch):
    monkeypatch.setattr(settings, "AI_ENABLED", True)
    monkeypatch.setattr(settings, "AI_PROVIDER", "openrouter")
    monkeypatch.setattr(settings, "OPENROUTER_API_KEY", "sk-test")

    captured = {}

    async def fake_post(self, url, headers=None, json=None):
        captured["url"] = url
        captured["headers"] = headers
        captured["json"] = json
        return _chat_response("graded: strong buy")

    monkeypatch.setattr(httpx.AsyncClient, "post", fake_post)

    client = AIClient()
    assert client.is_enabled is True
    out = await client.complete([{"role": "user", "content": "hi"}])
    assert out == "graded: strong buy"
    assert captured["url"].startswith("https://openrouter.ai")
    assert captured["headers"]["Authorization"] == "Bearer sk-test"


async def test_vllm_uses_configured_base_url(monkeypatch):
    monkeypatch.setattr(settings, "AI_ENABLED", True)
    monkeypatch.setattr(settings, "AI_PROVIDER", "vllm")
    monkeypatch.setattr(settings, "AI_VLLM_BASE_URL", "http://dgx-spark:8000/v1")

    captured = {}

    async def fake_post(self, url, headers=None, json=None):
        captured["url"] = url
        return _chat_response("ok")

    monkeypatch.setattr(httpx.AsyncClient, "post", fake_post)

    client = AIClient()
    assert client.is_enabled is True
    out = await client.complete([{"role": "user", "content": "hi"}])
    assert out == "ok"
    assert captured["url"] == "http://dgx-spark:8000/v1/chat/completions"


async def test_completion_degrades_gracefully_on_error(monkeypatch):
    monkeypatch.setattr(settings, "AI_ENABLED", True)
    monkeypatch.setattr(settings, "AI_PROVIDER", "openrouter")
    monkeypatch.setattr(settings, "OPENROUTER_API_KEY", "sk-test")

    async def boom_post(self, url, headers=None, json=None):
        raise httpx.ConnectError("down")

    monkeypatch.setattr(httpx.AsyncClient, "post", boom_post)
    out = await AIClient().complete([{"role": "user", "content": "hi"}])
    assert out is None
