"""story-4 (feature-006): read-only 'similar tracked items' endpoint.

Exercised on sqlite with the existing client/db fixtures and mocked embeddings.
Asserts ranked output when enabled and a clean empty/disabled shape when off —
no 500, no pgvector dependency.
"""
import pytest_asyncio

from app.core.config import settings
from app.models.tracked_item import TrackedItem


@pytest_asyncio.fixture
async def seeded(db):
    items = [
        TrackedItem(name="EPYC 7763", keywords="epyc 7763", embedding=[1.0, 0.0]),
        TrackedItem(name="EPYC 7713", keywords="epyc 7713", embedding=[0.95, 0.05]),
        TrackedItem(name="RTX A5000", keywords="rtx a5000", embedding=[0.0, 1.0]),
        TrackedItem(name="No embed", keywords="kw"),  # excluded (no embedding)
    ]
    db.add_all(items)
    await db.commit()
    for i in items:
        await db.refresh(i)
    return items


async def test_disabled_returns_clean_empty(monkeypatch, client, seeded):
    monkeypatch.setattr(settings, "ENABLE_SEMANTIC_MATCHING", False)
    monkeypatch.setattr(settings, "AI_ENABLED", True)
    anchor = seeded[0]
    resp = await client.get(f"/api/v1/semantic/similar/{anchor.id}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["enabled"] is False
    assert body["similar"] == []


async def test_ai_off_returns_clean_empty(monkeypatch, client, seeded):
    monkeypatch.setattr(settings, "ENABLE_SEMANTIC_MATCHING", True)
    monkeypatch.setattr(settings, "AI_ENABLED", False)
    anchor = seeded[0]
    resp = await client.get(f"/api/v1/semantic/similar/{anchor.id}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["enabled"] is False
    assert body["similar"] == []


async def test_enabled_returns_ranked(monkeypatch, client, seeded):
    monkeypatch.setattr(settings, "ENABLE_SEMANTIC_MATCHING", True)
    monkeypatch.setattr(settings, "AI_ENABLED", True)
    monkeypatch.setattr(settings, "OPENROUTER_API_KEY", "sk-test")  # makes AIClient enabled
    anchor = seeded[0]  # EPYC 7763, embedding [1,0]
    resp = await client.get(f"/api/v1/semantic/similar/{anchor.id}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["enabled"] is True
    names = [row["name"] for row in body["similar"]]
    # EPYC 7713 (close) ranks above RTX A5000 (orthogonal); anchor excluded.
    assert names[0] == "EPYC 7713"
    assert "EPYC 7763" not in names
    assert body["similar"][0]["similarity"] > body["similar"][-1]["similarity"]


async def test_unknown_item_404(monkeypatch, client, seeded):
    monkeypatch.setattr(settings, "ENABLE_SEMANTIC_MATCHING", True)
    monkeypatch.setattr(settings, "AI_ENABLED", True)
    monkeypatch.setattr(settings, "OPENROUTER_API_KEY", "sk-test")
    resp = await client.get("/api/v1/semantic/similar/999999")
    assert resp.status_code == 404
