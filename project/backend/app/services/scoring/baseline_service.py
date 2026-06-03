"""ScoringBaselineService: compute, degrade, and persist a per-item baseline.

feature-001 / ADR-001. Assembles total-price points for a tracked item from a
pluggable comp source, runs the pure stats core (``baseline_stats``) + the trend
signal, decides the snapshot ``source``, and upserts the single current
``ItemPriceBaseline`` row per item. When neither sold comps nor enough
PriceHistory points exist, it records a benchmark-sourced snapshot so the scoring
engine degrades to ``TrackedItem.benchmark_median``.

All thresholds are config-driven (BASELINE_LOOKBACK_DAYS / BASELINE_TUKEY_K /
BASELINE_MIN_POINTS / BASELINE_TREND_WINDOW_DAYS / BASELINE_TREND_THRESHOLD_PCT).

Sold-comps limitation (see findings.md): the eBay Browse *application* token
cannot return sold/completed listings — that needs the approval-gated
Marketplace Insights API. ``fetch_sold_comps`` is therefore a deliberately
separated, swappable seam that returns ``[]`` today; the baseline is built from
accumulated ``PriceHistory`` until real comps are wired in. Swapping
``fetch_sold_comps`` to real comps requires NO change to the stats math.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.item_price_baseline import ItemPriceBaseline
from app.models.price_history import PriceHistory
from app.models.tracked_item import TrackedItem
from app.services.scoring import baseline_stats

logger = logging.getLogger(__name__)


class ScoringBaselineService:
    """Builds + persists the rolling per-item market-history baseline."""

    def __init__(self) -> None:
        # Snapshot config once per instance; the daily job builds a fresh instance.
        self.lookback_days = settings.BASELINE_LOOKBACK_DAYS
        self.tukey_k = settings.BASELINE_TUKEY_K
        self.min_points = settings.BASELINE_MIN_POINTS
        self.trend_window_days = settings.BASELINE_TREND_WINDOW_DAYS
        self.trend_threshold_pct = settings.BASELINE_TREND_THRESHOLD_PCT

    async def fetch_sold_comps(self, item: TrackedItem) -> list[float]:
        """Real eBay sold/completed comps for ``item`` — the swappable seam.

        Returns ``[]`` today: the Browse *application* token has no access to
        sold/completed listings (needs the approval-gated Marketplace Insights
        API — see findings.md). Swap this to return real total-price comps and
        the stats math downstream is unchanged.
        """
        return []

    async def _price_history_points(
        self, db: AsyncSession, item: TrackedItem
    ) -> list[tuple[datetime, float]]:
        """Accumulated (timestamp, total_price) points within the lookback window."""
        since = datetime.utcnow() - timedelta(days=self.lookback_days)
        rows = (
            await db.execute(
                select(PriceHistory.timestamp, PriceHistory.total_price)
                .where(PriceHistory.tracked_item_id == item.id)
                .where(PriceHistory.timestamp >= since)
                .order_by(PriceHistory.timestamp.asc())
            )
        ).all()
        out: list[tuple[datetime, float]] = []
        for ts, total in rows:
            if ts is None or total is None:
                continue
            out.append((ts, float(total)))
        return out

    async def refresh_item(self, db: AsyncSession, item: TrackedItem) -> ItemPriceBaseline:
        """Compute + upsert the current baseline snapshot for one item.

        Source precedence: sold comps (if any) -> accumulated PriceHistory ->
        benchmark degrade. Always writes exactly one row per item (idempotent).
        """
        # 1) Try real sold comps first (empty today; swappable seam).
        comps = await self.fetch_sold_comps(item)
        source = "benchmark"
        stats: dict = {}
        trend_points: list[tuple[datetime, float]] = []

        if comps:
            stats = baseline_stats.compute_baseline(
                comps, k=self.tukey_k, min_points=self.min_points
            )
            if stats:
                source = "sold_comps"
                # Sold comps carry no timestamps here; trend stays from price history.

        # 2) Fall back to accumulated PriceHistory.
        history = await self._price_history_points(db, item)
        if not stats and history:
            hist_totals = [v for _, v in history]
            stats = baseline_stats.compute_baseline(
                hist_totals, k=self.tukey_k, min_points=self.min_points
            )
            if stats:
                source = "price_history"

        # Trend is computed from time-stamped history when available.
        trend_points = history
        trend_direction, trend_slope_pct = baseline_stats.trend_direction(
            trend_points,
            window_days=self.trend_window_days,
            threshold_pct=self.trend_threshold_pct,
        )

        row = await self._get_or_create(db, item.id)
        if stats:
            row.median_price = stats["median_price"]
            row.avg_price = stats["avg_price"]
            row.std_dev = stats["std_dev"]
            row.min_price = stats["min_price"]
            row.q1 = stats["q1"]
            row.q3 = stats["q3"]
            row.data_points = stats["data_points"]
        else:
            # Insufficient comps/history: degrade to catalog benchmark downstream.
            row.median_price = None
            row.avg_price = None
            row.std_dev = None
            row.min_price = None
            row.q1 = None
            row.q3 = None
            row.data_points = 0
        row.lookback_days = self.lookback_days
        row.trend_direction = trend_direction
        row.trend_slope_pct = trend_slope_pct
        row.source = source
        row.computed_at = datetime.utcnow()
        await db.flush()
        return row

    async def _get_or_create(self, db: AsyncSession, item_id: int) -> ItemPriceBaseline:
        existing = (
            await db.execute(
                select(ItemPriceBaseline).where(
                    ItemPriceBaseline.tracked_item_id == item_id
                )
            )
        ).scalar_one_or_none()
        if existing is not None:
            return existing
        row = ItemPriceBaseline(tracked_item_id=item_id, source="benchmark")
        db.add(row)
        return row

    async def refresh(self, db: AsyncSession) -> int:
        """Refresh every enabled tracked item; best-effort per item.

        Returns the number of items whose baseline was refreshed. A failure on
        one item is logged and skipped so the rest still refresh (used by the
        daily scheduler tick).
        """
        items = (
            await db.execute(
                select(TrackedItem).where(TrackedItem.is_enabled.is_(True))
            )
        ).scalars().all()
        refreshed = 0
        for item in items:
            try:
                await self.refresh_item(db, item)
                refreshed += 1
            except Exception:
                logger.exception("baseline refresh failed for item %s", getattr(item, "id", "?"))
        return refreshed
