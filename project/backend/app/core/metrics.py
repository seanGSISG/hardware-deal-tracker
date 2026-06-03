"""Prometheus metrics for the Hardware Deal Tracker.

Defines the domain metrics the Grafana dashboard queries and a helper to mount the
default HTTP instrumentation + /metrics endpoint. All metric names are prefixed
`hdt_` so they namespace cleanly alongside process/HTTP metrics.

Importing this module has no side effects beyond registering the collectors in the
global prometheus_client REGISTRY (idempotent within a process).
"""
from prometheus_client import Counter, Gauge, Histogram

# --- Poll pipeline ---------------------------------------------------------
POLL_CYCLES = Counter(
    "hdt_poll_cycles_total",
    "Number of poll cycles run (one per scheduler tick / trigger-all).",
)
POLL_TICK_DURATION = Histogram(
    "hdt_poll_tick_duration_seconds",
    "Wall-clock duration of a single scheduled poll tick.",
    buckets=(0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10, 30, 60),
)
LISTINGS_INGESTED = Counter(
    "hdt_listings_ingested_total",
    "New (non-duplicate) listings persisted across all polls.",
)
SCORING_RUNS = Counter(
    "hdt_scoring_runs_total",
    "Number of listings scored by the DealScoringEngine.",
)

# --- eBay client health ----------------------------------------------------
EBAY_ERRORS = Counter(
    "hdt_ebay_errors_total",
    "eBay API call failures (non-429 errors).",
)
EBAY_RATE_LIMITED = Counter(
    "hdt_ebay_rate_limited_total",
    "eBay API responses / local budget stops that signalled rate limiting (429).",
)

# --- Rate budget burn ------------------------------------------------------
RATE_BUDGET_CALLS_TODAY = Gauge(
    "hdt_rate_budget_calls_today",
    "eBay API calls consumed so far today.",
)
RATE_BUDGET_REMAINING = Gauge(
    "hdt_rate_budget_remaining",
    "eBay API calls remaining in today's budget.",
)
RATE_BUDGET_UTILIZATION = Gauge(
    "hdt_rate_budget_utilization_pct",
    "Percent of the daily eBay API budget consumed.",
)


def update_rate_budget(status: dict) -> None:
    """Mirror a RateBudgetManager.get_budget_status() dict into the gauges."""
    if "calls_today" in status:
        RATE_BUDGET_CALLS_TODAY.set(status["calls_today"])
    if "remaining" in status:
        RATE_BUDGET_REMAINING.set(status["remaining"])
    if "utilization_pct" in status:
        RATE_BUDGET_UTILIZATION.set(status["utilization_pct"])


def instrument_app(app) -> None:
    """Attach default HTTP instrumentation and expose GET /metrics.

    Uses prometheus-fastapi-instrumentator for request latency/count/size metrics
    and registers the /metrics scrape endpoint on the global registry (so the
    hdt_* domain metrics above are exported alongside it).
    """
    from prometheus_fastapi_instrumentator import Instrumentator

    Instrumentator().instrument(app).expose(
        app, endpoint="/metrics", include_in_schema=False
    )
