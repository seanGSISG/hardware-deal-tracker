"""story-2 (feature-006): gated, graceful embeddings path on AIClient.

Mirrors the complete() graceful-degradation contract: embed()/embed_batch()
return None / empty when AI is disabled or on any error, and only POST to the
provider's /embeddings endpoint when enabled. No real network call is made; the
httpx POST is monkeypatched.
"""
import httpx

from app.core.config import settings
from app.services.ai.client import AIClient


def _embedding_response(*vectors):
    class _Resp:
        def raise_for_status(self):
            pass

        def json(self):
            return {"data": [{"embedding": list(v)} for v in vectors]}

    return _Resp()


async def test_embed_returns_none_when_ai_disabled(monkeypatch):
    monkeypatch.setattr(settings, "AI_ENABLED", False)
    out = await AIClient().embed("EPYC 7763")
    assert out is None


async def test_embed_batch_empty_when_ai_disabled(monkeypatch):
    monkeypatch.setattr(settings, "AI_ENABLED", False)
    out = await AIClient().embed_batch(["a", "b"])
    assert out == []


async def test_embed_returns_vector_when_enabled(monkeypatch):
    monkeypatch.setattr(settings, "AI_ENABLED", True)
    monkeypatch.setattr(settings, "AI_PROVIDER", "openrouter")
    monkeypatch.setattr(settings, "OPENROUTER_API_KEY", "sk-test")
    monkeypatch.setattr(settings, "SEMANTIC_EMBEDDING_DIM", 3)

    captured = {}

    async def fake_post(self, url, headers=None, json=None):
        captured["url"] = url
        captured["headers"] = headers
        captured["json"] = json
        return _embedding_response([0.1, 0.2, 0.3])

    monkeypatch.setattr(httpx.AsyncClient, "post", fake_post)

    out = await AIClient().embed("EPYC 7763 256GB")
    assert out == [0.1, 0.2, 0.3]
    assert len(out) == settings.SEMANTIC_EMBEDDING_DIM
    # Uses the OpenRouter base + /embeddings endpoint and the same auth header.
    assert captured["url"].startswith("https://openrouter.ai")
    assert captured["url"].endswith("/embeddings")
    assert captured["headers"]["Authorization"] == "Bearer sk-test"
    assert captured["json"]["model"] == settings.SEMANTIC_EMBEDDING_MODEL
    assert captured["json"]["input"] == "EPYC 7763 256GB"


async def test_embed_batch_returns_vectors_when_enabled(monkeypatch):
    monkeypatch.setattr(settings, "AI_ENABLED", True)
    monkeypatch.setattr(settings, "AI_PROVIDER", "openrouter")
    monkeypatch.setattr(settings, "OPENROUTER_API_KEY", "sk-test")

    async def fake_post(self, url, headers=None, json=None):
        # Echo a vector per input.
        return _embedding_response([1.0, 0.0], [0.0, 1.0])

    monkeypatch.setattr(httpx.AsyncClient, "post", fake_post)

    out = await AIClient().embed_batch(["a", "b"])
    assert out == [[1.0, 0.0], [0.0, 1.0]]


async def test_embed_uses_vllm_base_url(monkeypatch):
    monkeypatch.setattr(settings, "AI_ENABLED", True)
    monkeypatch.setattr(settings, "AI_PROVIDER", "vllm")
    monkeypatch.setattr(settings, "AI_VLLM_BASE_URL", "http://dgx-spark:8000/v1")

    captured = {}

    async def fake_post(self, url, headers=None, json=None):
        captured["url"] = url
        return _embedding_response([0.5, 0.5])

    monkeypatch.setattr(httpx.AsyncClient, "post", fake_post)

    out = await AIClient().embed("hi")
    assert out == [0.5, 0.5]
    assert captured["url"] == "http://dgx-spark:8000/v1/embeddings"


async def test_embed_degrades_gracefully_on_error(monkeypatch):
    monkeypatch.setattr(settings, "AI_ENABLED", True)
    monkeypatch.setattr(settings, "AI_PROVIDER", "openrouter")
    monkeypatch.setattr(settings, "OPENROUTER_API_KEY", "sk-test")

    async def boom_post(self, url, headers=None, json=None):
        raise httpx.ConnectError("down")

    monkeypatch.setattr(httpx.AsyncClient, "post", boom_post)
    assert await AIClient().embed("x") is None
    assert await AIClient().embed_batch(["x", "y"]) == []


async def test_complete_path_unchanged(monkeypatch):
    """embed() must not disturb the existing complete() contract."""
    monkeypatch.setattr(settings, "AI_ENABLED", False)
    assert await AIClient().complete([{"role": "user", "content": "hi"}]) is None
