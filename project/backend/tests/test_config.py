"""Tests for app.core.config (story-001: SettingsConfigDict migration + scheduler vars)."""
import importlib
import warnings

from pydantic import PydanticDeprecatedSince20
from pydantic_settings import SettingsConfigDict

import app.core.config as config_module
from app.core.config import Settings


def test_scheduler_settings_defaults():
    s = Settings()
    assert s.SCHEDULER_ENABLED is True
    assert s.POLL_SCHEDULER_INTERVAL == 300


def test_scheduler_interval_env_override(monkeypatch):
    # Use a fresh (non-lru-cached) Settings instance to read the env override.
    monkeypatch.setenv("POLL_SCHEDULER_INTERVAL", "600")
    monkeypatch.setenv("SCHEDULER_ENABLED", "false")
    s = Settings()
    assert s.POLL_SCHEDULER_INTERVAL == 600
    assert s.SCHEDULER_ENABLED is False


def test_uses_settings_config_dict_not_class_config():
    # After migration there is no inner `class Config`; config lives in model_config.
    assert "Config" not in Settings.__dict__
    assert isinstance(Settings.model_config, dict)
    assert Settings.model_config.get("env_file") == ".env"
    assert Settings.model_config.get("case_sensitive") is True
    # Sanity: SettingsConfigDict is the construct we migrated to.
    assert SettingsConfigDict is not None


def test_no_class_based_config_deprecation_warning():
    # Reloading the module re-creates the Settings class; a class-based `Config`
    # would emit PydanticDeprecatedSince20 at class-definition time.
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        importlib.reload(config_module)
    class_config_warnings = [
        w for w in caught
        if issubclass(w.category, PydanticDeprecatedSince20)
        and "config" in str(w.message).lower()
    ]
    messages = [str(w.message) for w in class_config_warnings]
    assert not class_config_warnings, f"unexpected class-config deprecation: {messages}"


def test_existing_fields_preserved():
    s = Settings()
    # A representative slice of pre-existing fields must remain with identical defaults.
    assert s.DATABASE_URL.startswith("postgresql+asyncpg://")
    assert s.SECRET_KEY == "change-me-in-production-min-32-chars"
    assert s.ALGORITHM == "HS256"
    assert s.ACCESS_TOKEN_EXPIRE_MINUTES == 30
    assert s.EBAY_DAILY_CALL_LIMIT == 5000
    assert s.EBAY_CALL_BUFFER == 200
    assert s.EBAY_NEAR_LIMIT_THRESHOLD == 4000
    assert s.USE_MOCK_EBAY is True
    assert s.FRONTEND_URL == "http://localhost:3000"


def test_get_settings_is_cached():
    from app.core.config import get_settings
    assert get_settings() is get_settings()


def test_feature003_settings_defaults():
    """story-T2.0: feature-003 adds notification/auth config fields."""
    s = Settings()
    assert s.NOTIFICATIONS_ENABLED is True
    assert s.SMTP_FROM == ""
    assert s.ALLOW_REGISTRATION is False


def test_feature003_settings_env_override(monkeypatch):
    monkeypatch.setenv("NOTIFICATIONS_ENABLED", "false")
    monkeypatch.setenv("SMTP_FROM", "deals@example.com")
    monkeypatch.setenv("ALLOW_REGISTRATION", "true")
    s = Settings()
    assert s.NOTIFICATIONS_ENABLED is False
    assert s.SMTP_FROM == "deals@example.com"
    assert s.ALLOW_REGISTRATION is True
