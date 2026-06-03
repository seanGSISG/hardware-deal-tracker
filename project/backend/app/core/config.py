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

    # AI deal analysis (feature-006). Opt-in; configurable provider.
    AI_ENABLED: bool = False
    AI_PROVIDER: str = "openrouter"  # "openrouter" | "vllm"
    AI_MODEL: str = ""  # falls back to OPENROUTER_MODEL when empty
    AI_VLLM_BASE_URL: str = ""  # OpenAI-compatible base url for local vLLM (DGX Spark)

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

    # Scheduler (feature-001 owns this block; other features add vars on top)
    SCHEDULER_ENABLED: bool = True
    POLL_SCHEDULER_INTERVAL: int = 300

    # Notifications + Auth (feature-003)
    NOTIFICATIONS_ENABLED: bool = True
    SMTP_FROM: str = ""
    ALLOW_REGISTRATION: bool = False

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

    # CORS (feature-002 / ADR-002). Credentialed cookie auth requires an explicit
    # origin allowlist (wildcard "*" is forbidden with allow_credentials=True).
    # Exact origins live here; *.lab.lsdmt.me subdomains are matched via the regex
    # in main.py (CORSMiddleware allow_origins cannot wildcard subdomains).
    # Override with a JSON array or comma-separated env value (CORS_ALLOW_ORIGINS).
    CORS_ALLOW_ORIGINS: list[str] = [
        "http://localhost:3000",
        "https://lab.lsdmt.me",
    ]
    # Regex applied IN ADDITION to the list above so any https://<sub>.lab.lsdmt.me
    # origin is accepted without enumerating every subdomain.
    CORS_ALLOW_ORIGIN_REGEX: str = r"https://([a-z0-9-]+\.)*lab\.lsdmt\.me"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
