"""Configurable AI client for deal analysis (feature-006).

Talks to any OpenAI-compatible chat-completions endpoint, so the same code path
serves OpenRouter (default) and a local vLLM server on the DGX Spark (opt-in via
AI_PROVIDER=vllm + AI_VLLM_BASE_URL). AI is opt-in (AI_ENABLED) and every call
degrades gracefully to None so the poll/score path never depends on it.
"""
import logging

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

OPENROUTER_BASE = "https://openrouter.ai/api/v1"
OPENROUTER_URL = OPENROUTER_BASE + "/chat/completions"
OPENROUTER_EMBEDDINGS_URL = OPENROUTER_BASE + "/embeddings"


class AIClient:
    @property
    def is_enabled(self) -> bool:
        if not settings.AI_ENABLED:
            return False
        if settings.AI_PROVIDER == "vllm":
            return bool(settings.AI_VLLM_BASE_URL)
        if settings.AI_PROVIDER == "openrouter":
            return bool(settings.OPENROUTER_API_KEY)
        return False

    @property
    def model(self) -> str:
        return settings.AI_MODEL or settings.OPENROUTER_MODEL

    def _endpoint(self) -> str:
        if settings.AI_PROVIDER == "vllm":
            return settings.AI_VLLM_BASE_URL.rstrip("/") + "/chat/completions"
        return OPENROUTER_URL

    def _embeddings_endpoint(self) -> str:
        if settings.AI_PROVIDER == "vllm":
            return settings.AI_VLLM_BASE_URL.rstrip("/") + "/embeddings"
        return OPENROUTER_EMBEDDINGS_URL

    def _headers(self) -> dict:
        headers = {"Content-Type": "application/json"}
        if settings.AI_PROVIDER == "openrouter":
            headers["Authorization"] = f"Bearer {settings.OPENROUTER_API_KEY}"
        return headers

    async def complete(
        self, messages: list[dict], *, temperature: float = 0.2, max_tokens: int = 512
    ) -> str | None:
        """Return the assistant message content, or None if disabled / on any error."""
        if not self.is_enabled:
            return None
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(self._endpoint(), headers=self._headers(), json=payload)
                resp.raise_for_status()
                data = resp.json()
                return data["choices"][0]["message"]["content"]
        except Exception:
            logger.exception("AI completion failed (provider=%s)", settings.AI_PROVIDER)
            return None

    # --- Embeddings (feature-006, ADR-006) ----------------------------------
    # OPTIONAL semantic-matching path. Same provider/base-url/header resolution
    # as complete(); same graceful-degradation contract (None / [] on disabled
    # or any error). Never raises into the caller.

    async def embed(self, text: str) -> list[float] | None:
        """Embed a single string, or None if AI is disabled / on any error."""
        result = await self.embed_batch([text])
        return result[0] if result else None

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Embed a batch of strings via the provider's /embeddings endpoint.

        Returns one vector per input when enabled, or [] when AI is disabled,
        the provider has no creds/base-url, the input is empty, or on any
        HTTP/parse error. No exception ever propagates.
        """
        if not self.is_enabled or not texts:
            return []
        payload = {
            "model": settings.SEMANTIC_EMBEDDING_MODEL,
            "input": texts[0] if len(texts) == 1 else texts,
        }
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(
                    self._embeddings_endpoint(), headers=self._headers(), json=payload
                )
                resp.raise_for_status()
                data = resp.json()
                return [row["embedding"] for row in data["data"]]
        except Exception:
            logger.exception("AI embedding failed (provider=%s)", settings.AI_PROVIDER)
            return []
