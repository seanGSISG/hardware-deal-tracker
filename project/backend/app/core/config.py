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

    # ntfy (self-hosted push). Publishing to the homelab ntfy requires auth, so
    # either NTFY_TOKEN (Bearer) or NTFY_USERNAME/NTFY_PASSWORD (basic) is needed.
    NTFY_BASE_URL: str = ""
    NTFY_TOPIC: str = ""
    NTFY_TOKEN: str = ""
    NTFY_USERNAME: str = ""
    NTFY_PASSWORD: str = ""

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

    # Activity log (search_log audit table). Rows older than the retention window
    # are pruned by a daily scheduler job so the table stays bounded.
    SEARCH_LOG_RETENTION_DAYS: int = 14
    SEARCH_LOG_PRUNE_HOUR: int = 4

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

    # Sold-comps rolling baseline (feature-001, ADR-001). All additive.
    # Rolling-window Tukey-trimmed median/IQR + 30d trend, persisted per item and
    # refreshed by a daily scheduler job; degrades to catalog benchmark_median.
    BASELINE_LOOKBACK_DAYS: int = 90
    BASELINE_TUKEY_K: float = 1.5
    BASELINE_MIN_POINTS: int = 5
    BASELINE_TREND_WINDOW_DAYS: int = 30
    BASELINE_TREND_THRESHOLD_PCT: float = 0.05
    BASELINE_REFRESH_ENABLED: bool = True
    BASELINE_REFRESH_HOUR: int = 6

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

    # --- Semantic catalog matching (feature-006, ADR-006, APPENDED) ----------
    # STRETCH / OPTIONAL: pgvector-backed embedding similarity that improves
    # listing->catalog attribution and powers a "similar tracked items"
    # affordance. The whole feature is gated behind ENABLE_SEMANTIC_MATCHING
    # (default false) AND AI_ENABLED, and degrades to a no-op when either is off
    # or embeddings are unavailable. When enabled, the Postgres service must use
    # the pgvector/pgvector:pg17 image (the migration creates the extension).
    # The in-memory sqlite test DB cannot load pgvector, so the embedding column
    # is dialect-guarded (JSON on sqlite) and embeddings are mocked in tests.
    ENABLE_SEMANTIC_MATCHING: bool = False
    # OpenAI-compatible embeddings model (OpenRouter default; vLLM opt-in via
    # AI_PROVIDER=vllm + AI_VLLM_BASE_URL, reusing the AIClient provider path).
    SEMANTIC_EMBEDDING_MODEL: str = "openai/text-embedding-3-small"
    # Embedding dimension. MUST match both the model output and the pgvector
    # column width. text-embedding-3-small -> 1536.
    SEMANTIC_EMBEDDING_DIM: int = 1536
    # Minimum cosine similarity for a catalog suggestion to be returned.
    SEMANTIC_MIN_SIMILARITY: float = 0.5
    # Default top-N for the "similar tracked items" affordance.
    SEMANTIC_SIMILAR_TOP_N: int = 5

    # --- Community-signal ingestion (feature-007, ADR-007, APPENDED) ----------
    # STRETCH. A DISTINCT leads pipeline (Reddit r/homelabsales, optional STH)
    # that AI-extracts structured fields from unstructured peer-to-peer posts into
    # a separate LEADS surface — NEVER routed through scoring/notifications.
    # Gated OFF by default: when ENABLE_COMMUNITY_SIGNAL is False the feature is
    # fully dormant (no scheduler job, no network, no AI, endpoint reports
    # disabled) and the app behaves byte-for-byte unchanged.
    ENABLE_COMMUNITY_SIGNAL: bool = False
    # Polite self-imposed daily call bucket for community sources, separate from
    # eBay's 5000/day RateBudgetManager (uses the per-source SourceRateBudget).
    COMMUNITY_SIGNAL_DAILY_LIMIT: int = 200
    # How many newest posts to pull per ingest cycle.
    COMMUNITY_SIGNAL_FETCH_LIMIT: int = 50
    # Optional in-process ingest cadence (seconds) when the feature is enabled.
    COMMUNITY_SIGNAL_INTERVAL: int = 1800

    # Reddit OAuth (script-app / app-only). All optional; the Reddit client
    # degrades to [] when client id/secret are absent. user/password enable the
    # password grant; without them the client uses the app-only client_credentials
    # grant. Nothing is hardcoded.
    REDDIT_CLIENT_ID: str = ""
    REDDIT_CLIENT_SECRET: str = ""
    REDDIT_USER_AGENT: str = "hardware-deal-tracker/0.2 (community-signal)"
    REDDIT_USERNAME: str = ""
    REDDIT_PASSWORD: str = ""
    REDDIT_SUBREDDIT: str = "homelabsales"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
