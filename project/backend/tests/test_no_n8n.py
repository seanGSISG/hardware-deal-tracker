"""T3.1 — n8n is removed from the stack.

n8n was never wired into the data flow (APScheduler now owns polling). Its service,
volume, and env vars are dead weight and an extra attack surface, so they must be gone
from docker-compose.yml and .env.example.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
COMPOSE = ROOT / "docker-compose.yml"
ENV_EXAMPLE = ROOT / ".env.example"


def test_compose_has_no_n8n_service_or_volume():
    text = COMPOSE.read_text().lower()
    assert "n8n" not in text, "n8n still referenced in docker-compose.yml"
    assert "n8n_data" not in text


def test_env_example_has_no_n8n_vars():
    text = ENV_EXAMPLE.read_text()
    assert "N8N_" not in text, "N8N_* vars still in .env.example"
    assert "n8n" not in text.lower()


def test_remaining_services_present():
    text = COMPOSE.read_text()
    for svc in ("postgres:", "redis:", "backend:", "frontend:"):
        assert svc in text, f"expected service {svc} to remain"
