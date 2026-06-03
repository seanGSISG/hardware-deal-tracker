import logging
from contextlib import asynccontextmanager

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import router as api_router
from app.core import metrics
from app.core.config import settings
from app.core.security import validate_secret_key
from app.db.session import session_factory
from app.services.ebay.poller import EbayPoller
from app.services.notifications.digest import DigestService
from app.services.scoring.baseline_service import ScoringBaselineService

logger = logging.getLogger(__name__)

# Configure the root logger so the app's operational logs (scheduler start, poll
# ticks, digest/baseline runs, community ingest) are actually emitted. Without
# this, `logger.info(...)` calls are dropped because uvicorn only configures its
# own loggers. Honors LOG_LEVEL from settings; idempotent (force=True) so repeated
# imports under multiple workers don't stack handlers.
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    force=True,
)


async def _poll_tick() -> None:
    """One scheduled poll cycle: open a fresh session, poll+score, commit.

    Runs inside the in-process scheduler (ADR-001). Any failure is caught and
    logged so a single bad tick never tears down the scheduler.
    """
    metrics.POLL_CYCLES.inc()
    try:
        with metrics.POLL_TICK_DURATION.time():
            async with session_factory() as db:
                poller = EbayPoller()
                result = await poller.search_all(db)
                await db.commit()
                try:
                    metrics.update_rate_budget(await poller.budget.get_budget_status())
                except Exception:  # noqa: BLE001 — metrics must never break a poll tick
                    logger.debug("rate-budget metrics update failed", exc_info=True)
        new_count = result.get("total_new") or 0
        metrics.LISTINGS_INGESTED.inc(new_count)
        metrics.SCORING_RUNS.inc(new_count)
        logger.info(
            "poll tick: processed=%s skipped=%s new=%s",
            result.get("items_processed"),
            result.get("items_skipped"),
            result.get("total_new"),
        )
    except Exception:
        metrics.EBAY_ERRORS.inc()
        logger.exception("poll tick failed")


async def _digest_tick(mode: str) -> None:
    """One scheduled email-digest cycle for a given cadence ('daily'/'weekly').

    Best-effort: any failure is caught and logged so a bad digest run never
    tears down the scheduler.
    """
    try:
        async with session_factory() as db:
            sent = await DigestService().run(db, mode=mode)
            await db.commit()
        logger.info("digest tick (%s): sent=%s", mode, sent)
    except Exception:
        logger.exception("digest tick (%s) failed", mode)


async def _baseline_refresh_tick() -> None:
    """One scheduled daily baseline refresh (feature-001, ADR-001).

    Opens a fresh session, recomputes + upserts the rolling ItemPriceBaseline
    snapshot for every enabled tracked item, then commits. Best-effort: a single
    bad item is caught inside ScoringBaselineService.refresh, and any top-level
    failure is caught here so a bad run never tears down the scheduler. Mirrors
    the _poll_tick / _digest_tick pattern.
    """
    try:
        async with session_factory() as db:
            refreshed = await ScoringBaselineService().refresh(db)
            await db.commit()
        logger.info("baseline refresh tick: refreshed=%s", refreshed)
    except Exception:
        logger.exception("baseline refresh tick failed")


async def _community_ingest_tick() -> None:
    """One scheduled community-signal ingest cycle (feature-007, ADR-007).

    Only ever registered when ENABLE_COMMUNITY_SIGNAL is True. Opens a fresh
    session, runs the gated CommunitySignalSource leads pipeline (fetch ->
    AI-extract -> sold/traded filter -> dedup -> persist) and commits. Best-effort:
    any failure is caught and logged so a bad run never tears down the scheduler.
    NEVER routes through scoring/notifications. Mirrors the _poll_tick pattern.
    """
    try:
        from app.services.community.source import CommunitySignalSource

        async with session_factory() as db:
            leads = await CommunitySignalSource().ingest(db)
            await db.commit()
        logger.info("community ingest tick: leads=%s", len(leads))
    except Exception:
        logger.exception("community ingest tick failed")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Start/stop the in-process poll scheduler around the app lifecycle."""
    # Fail loud before serving any request if SECRET_KEY is misconfigured (T2.6).
    validate_secret_key()
    scheduler = None
    if settings.SCHEDULER_ENABLED:
        scheduler = AsyncIOScheduler()
        scheduler.add_job(
            _poll_tick,
            trigger=IntervalTrigger(seconds=settings.POLL_SCHEDULER_INTERVAL),
            id="poll_tick",
            coalesce=True,
            max_instances=1,
            replace_existing=True,
        )
        if settings.NOTIFICATIONS_ENABLED:
            # Distinct job ids so they never collide with poll_tick.
            scheduler.add_job(
                _digest_tick,
                trigger=CronTrigger(hour=8, minute=0),  # daily 08:00
                args=["daily"],
                id="digest_tick",
                coalesce=True,
                max_instances=1,
                replace_existing=True,
            )
            scheduler.add_job(
                _digest_tick,
                trigger=CronTrigger(day_of_week="mon", hour=8, minute=0),  # weekly Mon 08:00
                args=["weekly"],
                id="digest_tick_weekly",
                coalesce=True,
                max_instances=1,
                replace_existing=True,
            )
        if settings.BASELINE_REFRESH_ENABLED:
            # Daily rolling-baseline refresh (feature-001). Distinct id so it
            # never collides with poll_tick/digest_tick. Cron hour from config.
            scheduler.add_job(
                _baseline_refresh_tick,
                trigger=CronTrigger(hour=settings.BASELINE_REFRESH_HOUR, minute=0),
                id="baseline_refresh_tick",
                coalesce=True,
                max_instances=1,
                replace_existing=True,
            )
        if settings.ENABLE_COMMUNITY_SIGNAL:
            # Gated community-signal ingest (feature-007). Distinct id; only
            # registered when the flag is on, so the default app schedules no
            # community job and behaves byte-for-byte unchanged.
            scheduler.add_job(
                _community_ingest_tick,
                trigger=IntervalTrigger(seconds=settings.COMMUNITY_SIGNAL_INTERVAL),
                id="community_ingest_tick",
                coalesce=True,
                max_instances=1,
                replace_existing=True,
            )
        scheduler.start()
        logger.info(
            "poll scheduler started (interval=%ss)", settings.POLL_SCHEDULER_INTERVAL
        )
    app.state.scheduler = scheduler
    try:
        yield
    finally:
        if scheduler is not None:
            scheduler.shutdown(wait=False)
            logger.info("poll scheduler stopped")


app = FastAPI(
    title="Hardware Deal Tracker",
    description="AI-Powered Enterprise Hardware Deal Tracking API",
    version="0.2.0",
    docs_url="/api/v1/docs",
    openapi_url="/api/v1/openapi.json",
    lifespan=lifespan,
)

# Credentialed CORS (ADR-002): the httpOnly session cookie requires an explicit
# origin allowlist (no "*" with allow_credentials=True). Exact origins come from
# CORS_ALLOW_ORIGINS; *.lab.lsdmt.me subdomains are matched via allow_origin_regex
# since CORSMiddleware.allow_origins cannot wildcard subdomains.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ALLOW_ORIGINS,
    allow_origin_regex=settings.CORS_ALLOW_ORIGIN_REGEX,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)

# Prometheus: default HTTP metrics + GET /metrics exposing the hdt_* domain metrics.
metrics.instrument_app(app)


@app.get("/")
async def root():
    return {"message": "Hardware Deal Tracker API", "docs": "/api/v1/docs", "version": "0.2.0"}
