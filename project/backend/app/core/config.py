from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)

    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/hardware_tracker"
    REDIS_URL: str = "redis://localhost:6379/0"
    SECRET_KEY: str = "change-me-in-production-min-32-chars"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # eBay
    EBAY_APP_ID: str = ""
    EBAY_CERT_ID: str = ""
    EBAY_DEV_ID: str = ""
    EBAY_REDIRECT_URI: str = ""

    # Rate Limiting
    EBAY_DAILY_CALL_LIMIT: int = 5000
    EBAY_CALL_BUFFER: int = 200
    EBAY_NEAR_LIMIT_THRESHOLD: int = 4000

    # OpenRouter
    OPENROUTER_API_KEY: str = ""
    OPENROUTER_MODEL: str = "mistralai/mistral-small-3.1-24b-instruct"

    # Telegram
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_CHAT_ID: str = ""

    # SMTP
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""

    # App
    BACKEND_PORT: int = 8000
    LOG_LEVEL: str = "INFO"
    USE_MOCK_EBAY: bool = True
    FRONTEND_URL: str = "http://localhost:3000"
    N8N_WEBHOOK_URL: str = "http://n8n:5678/webhook"

    # Scheduler (feature-001 owns this block; other features add vars on top)
    SCHEDULER_ENABLED: bool = True
    POLL_SCHEDULER_INTERVAL: int = 300

    # Multi-source ingestion (feature-005)
    # PCPartPicker is a BENCHMARK-only source; OFF by default (ToS-sensitive,
    # anti-bot). Its own polite daily bucket, separate from eBay's 5000/day.
    ENABLE_PCPARTPICKER: bool = False
    PCPARTPICKER_DAILY_LIMIT: int = 200
    PCPARTPICKER_CIRCUIT_BREAKER_THRESHOLD: int = 3
    PCPARTPICKER_REGION: str = "us"
    # Generic Shopify JSON-LD adapters: enable + per-source polite daily bucket.
    ENABLE_SHOPIFY_SOURCES: bool = False
    SHOPIFY_SOURCE_DAILY_LIMIT: int = 100


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
