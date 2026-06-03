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

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


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
