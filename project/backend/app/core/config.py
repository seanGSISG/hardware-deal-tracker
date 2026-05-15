from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
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

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
