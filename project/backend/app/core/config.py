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

    # --- Per-store Shopify config (feature-003, APPENDED) --------------------
    # Each onboarded retailer has an independent enable flag (defaults below
    # follow the robots.txt/ToS verification ledger in
    # docs/SOURCE_ONBOARDING.md), an optional base_url override, and an optional
    # per-store daily-limit override. A store is only polled when it is BOTH
    # globally enabled (ENABLE_SHOPIFY_SOURCES) AND per-store enabled AND
    # robots/ToS-verified in the registry. SaveMyServer is a low-cadence price
    # MEMORY signal (smaller bucket) rather than a hot deal feed.
    SHOPIFY_TECHMIKENY_ENABLED: bool = True
    SHOPIFY_TECHMIKENY_BASE_URL: str = ""
    SHOPIFY_TECHMIKENY_DAILY_LIMIT: int = 0  # 0 -> use registry default

    SHOPIFY_UNIXSURPLUS_ENABLED: bool = True
    SHOPIFY_UNIXSURPLUS_BASE_URL: str = ""
    SHOPIFY_UNIXSURPLUS_DAILY_LIMIT: int = 0

    SHOPIFY_SERVERMONKEY_ENABLED: bool = True
    SHOPIFY_SERVERMONKEY_BASE_URL: str = ""
    SHOPIFY_SERVERMONKEY_DAILY_LIMIT: int = 0

    SHOPIFY_CLOUD_NINJAS_ENABLED: bool = True
    SHOPIFY_CLOUD_NINJAS_BASE_URL: str = ""
    SHOPIFY_CLOUD_NINJAS_DAILY_LIMIT: int = 0

    SHOPIFY_NATEX_ENABLED: bool = True
    SHOPIFY_NATEX_BASE_URL: str = ""
    SHOPIFY_NATEX_DAILY_LIMIT: int = 0

    SHOPIFY_SAVEMYSERVER_ENABLED: bool = True
    SHOPIFY_SAVEMYSERVER_BASE_URL: str = ""
    SHOPIFY_SAVEMYSERVER_DAILY_LIMIT: int = 0  # registry sets a low memory-signal cadence

    # --- PCPartPicker residential egress (feature-003, story-5, APPENDED) ----
    # PCPartPicker calls must route through a RESIDENTIAL Tailscale exit node,
    # never a datacenter IP (ToS + Cloudflare anti-bot). refresh_benchmark only
    # runs when ENABLE_PCPARTPICKER is true AND this egress is configured.
    PCPARTPICKER_USE_RESIDENTIAL_EGRESS: bool = False
    PCPARTPICKER_TAILSCALE_EXIT_NODE: str = ""  # e.g. "home-residential" exit-node name/IP


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
