"""feature-001 story-002: trend-direction signal from rolling-window slope.

TDD: written FIRST. Least-squares slope of total_price vs. time over the last N
days, expressed as a percent change across the window, classified rising
(> +threshold) / falling (< -threshold) / stable. Returns (direction, slope_pct).
"""
from datetime import datetime, timedelta

import pytest

from app.services.scoring import baseline_stats


def _series(values, *, end=None, step_days=1):
    """Build (timestamp, value) points oldest->newest ending at `end`."""
    end = end or datetime(2026, 6, 1, 12, 0, 0)
    n = len(values)
    return [
        (end - timedelta(days=step_days * (n - 1 - i)), float(v))
        for i, v in enumerate(values)
    ]


def test_clearly_rising_series_returns_rising():
    pts = _series([100, 110, 120, 130, 140, 150])
    direction, slope_pct = baseline_stats.trend_direction(pts, window_days=30, threshold_pct=0.05)
    assert direction == "rising"
    assert slope_pct > 0.05


def test_clearly_falling_series_returns_falling():
    pts = _series([150, 140, 130, 120, 110, 100])
    direction, slope_pct = baseline_stats.trend_direction(pts, window_days=30, threshold_pct=0.05)
    assert direction == "falling"
    assert slope_pct < -0.05


def test_flat_series_returns_stable():
    pts = _series([100, 100, 100, 100, 100])
    direction, slope_pct = baseline_stats.trend_direction(pts, window_days=30, threshold_pct=0.05)
    assert direction == "stable"
    assert slope_pct == pytest.approx(0.0, abs=1e-9)


def test_noisy_within_threshold_is_stable():
    # Small wiggles well under +/-5% across the window.
    pts = _series([100, 101, 99, 100.5, 100, 99.5])
    direction, _ = baseline_stats.trend_direction(pts, window_days=30, threshold_pct=0.05)
    assert direction == "stable"


def test_near_boundary_classifies_on_correct_side_of_threshold():
    # ~ +8% rise across the window -> rising under a 5% threshold, stable under a 10% one.
    pts = _series([100, 102, 104, 106, 108])
    rising, slope = baseline_stats.trend_direction(pts, window_days=30, threshold_pct=0.05)
    assert rising == "rising"
    stable, _ = baseline_stats.trend_direction(pts, window_days=30, threshold_pct=0.10)
    assert stable == "stable"


def test_threshold_is_a_parameter():
    pts = _series([100, 103, 106])  # ~ +6% across window
    assert baseline_stats.trend_direction(pts, threshold_pct=0.05)[0] == "rising"
    assert baseline_stats.trend_direction(pts, threshold_pct=0.20)[0] == "stable"


def test_window_days_filters_old_points():
    # Old crash point far outside a 30d window must not drag the trend.
    end = datetime(2026, 6, 1, 12, 0, 0)
    recent = _series([100, 100, 100], end=end, step_days=1)
    old = [(end - timedelta(days=200), 10.0)]
    pts = old + recent
    direction, _ = baseline_stats.trend_direction(pts, window_days=30, threshold_pct=0.05)
    assert direction == "stable"


def test_empty_and_single_point_do_not_raise():
    assert baseline_stats.trend_direction([], window_days=30, threshold_pct=0.05)[0] == "stable"
    one = [(datetime(2026, 6, 1, 12, 0, 0), 100.0)]
    assert baseline_stats.trend_direction(one, window_days=30, threshold_pct=0.05)[0] == "stable"


def test_returns_direction_label_and_numeric_slope_pct():
    pts = _series([100, 120, 140])
    result = baseline_stats.trend_direction(pts, window_days=30, threshold_pct=0.05)
    assert isinstance(result, tuple) and len(result) == 2
    direction, slope_pct = result
    assert direction in ("rising", "falling", "stable")
    assert isinstance(slope_pct, float)
