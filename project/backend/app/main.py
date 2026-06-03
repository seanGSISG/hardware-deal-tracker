import logging
from contextlib import asynccontextmanager

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import router as api_router
from app.core.config import settings
from app.core.security import validate_secret_key
from app.db.session import session_factory
from app.services.ebay.poller import EbayPoller
from app.services.notifications.digest import DigestService

logger = logging.getLogger(__name__)


async def _poll_tick() -> None:
    """One scheduled poll cycle: open a fresh session, poll+score, commit.

    Runs inside the in-process scheduler (ADR-001). Any failure is caught and
    logged so a single bad tick never tears down the scheduler.
    """
    try:
        async with session_factory() as db:
            poller = EbayPoller()
            result = await poller.search_all(db)
            await db.commit()
        logger.info(
            "poll tick: processed=%s skipped=%s new=%s",
            result.get("items_processed"),
            result.get("items_skipped"),
            result.get("total_new"),
        )
    except Exception:
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

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.get("/")
async def root():
    return {"message": "Hardware Deal Tracker API", "docs": "/api/v1/docs", "version": "0.2.0"}
