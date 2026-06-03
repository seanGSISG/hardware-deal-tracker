"""Pure statistical core for the rolling sold-comps baseline (feature-001).

Reimplements the *idea* of the bullseye-app sold-comps pattern — a Tukey
IQR-fence trim followed by a robust median + IQR + summary stats over a rolling
window of total-price points — from first principles. No AGPL code is copied.

This module is intentionally pure: it imports nothing from app.db /
app.services.ebay / app.services.sources and performs no I/O, so it is trivially
unit-testable on plain lists of floats. Higher layers (ScoringBaselineService)
supply the price points and the config-driven parameters (lookback / k /
min_points / trend window+threshold).

The returned dict uses byte-for-byte the keys ``DealScoringEngine`` already
reads — ``median_price``, ``avg_price``, ``std_dev``, ``min_price``,
``data_points`` — plus ``q1`` / ``q3`` for surfacing the IQR band.
"""
from __future__ import annotations

import statistics
from collections.abc import Iterable, Sequence
from datetime import datetime, timedelta


def _quantile(sorted_values: Sequence[float], q: float) -> float:
    """Linear-interpolation quantile (numpy 'linear' / type-7), pure-Python.

    ``sorted_values`` must already be ascending and non-empty. ``q`` in [0, 1].
    """
    n = len(sorted_values)
    if n == 1:
        return float(sorted_values[0])
    pos = q * (n - 1)
    lo = int(pos)
    hi = min(lo + 1, n - 1)
    frac = pos - lo
    return float(sorted_values[lo]) + (float(sorted_values[hi]) - float(sorted_values[lo])) * frac


def tukey_trim(values: Iterable[float], k: float = 1.5) -> list[float]:
    """Drop points outside the Tukey fence [Q1 - k*IQR, Q3 + k*IQR].

    Returns the in-fence points (order not guaranteed). With < 2 points the fence
    is undefined, so the input is returned unchanged.
    """
    vals = [float(v) for v in values]
    if len(vals) < 2:
        return vals
    ordered = sorted(vals)
    q1 = _quantile(ordered, 0.25)
    q3 = _quantile(ordered, 0.75)
    iqr = q3 - q1
    lower = q1 - k * iqr
    upper = q3 + k * iqr
    return [v for v in vals if lower <= v <= upper]


def compute_baseline(
    values: Iterable[float],
    *,
    k: float = 1.5,
    min_points: int = 5,
) -> dict | None:
    """Tukey-trim ``values`` then compute the engine-shaped baseline dict.

    Parameters
    ----------
    values:
        Total-price points (price + shipping) over the rolling window.
    k:
        Tukey fence factor (config: BASELINE_TUKEY_K). Not a hard-coded literal.
    min_points:
        Insufficiency guard (config: BASELINE_MIN_POINTS). When fewer than this
        many points remain *after trimming*, returns ``{}`` so callers degrade to
        the catalog ``benchmark_median``.

    Returns
    -------
    dict with keys ``median_price``, ``avg_price``, ``std_dev`` (population),
    ``min_price``, ``data_points``, ``q1``, ``q3`` — or ``{}`` when insufficient.
    """
    trimmed = tukey_trim(values, k=k)
    if len(trimmed) < max(min_points, 1):
        return {}

    ordered = sorted(trimmed)
    n = len(ordered)
    return {
        "median_price": float(statistics.median(ordered)),
        "avg_price": float(statistics.fmean(ordered)),
        "std_dev": float(statistics.pstdev(ordered)) if n > 1 else 0.0,
        "min_price": float(ordered[0]),
        "data_points": n,
        "q1": _quantile(ordered, 0.25),
        "q3": _quantile(ordered, 0.75),
    }


def trend_direction(
    points: Iterable[tuple[datetime, float]],
    *,
    window_days: int = 30,
    threshold_pct: float = 0.05,
) -> tuple[str, float]:
    """Classify the recent price trend from a least-squares slope.

    Fits ``value = a + b*t`` (t in days) over the points within the last
    ``window_days`` (relative to the newest point), expresses the predicted
    change across the observed span as a fraction of the fitted start level, and
    classifies:

      * ``rising``  when slope_pct >  +threshold_pct
      * ``falling`` when slope_pct <  -threshold_pct
      * ``stable``  otherwise

    Parameters ``window_days`` and ``threshold_pct`` are config-wired by callers
    (BASELINE_TREND_WINDOW_DAYS / BASELINE_TREND_THRESHOLD_PCT), never hard-coded.

    Returns ``(direction, slope_pct)``. With 0 or 1 in-window points it does not
    raise and returns ``("stable", 0.0)``.
    """
    pts = [(ts, float(v)) for ts, v in points]
    if not pts:
        return ("stable", 0.0)

    newest = max(ts for ts, _ in pts)
    cutoff = newest - timedelta(days=window_days)
    window = [(ts, v) for ts, v in pts if ts >= cutoff]
    if len(window) < 2:
        return ("stable", 0.0)

    earliest = min(ts for ts, _ in window)
    # x in days since the earliest in-window point; y is total price.
    xs = [(ts - earliest).total_seconds() / 86400.0 for ts, _ in window]
    ys = [v for _, v in window]
    n = len(window)

    mean_x = sum(xs) / n
    mean_y = sum(ys) / n
    sxx = sum((x - mean_x) ** 2 for x in xs)
    if sxx == 0:  # all timestamps identical -> no time axis to fit
        return ("stable", 0.0)
    sxy = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys, strict=True))
    slope = sxy / sxx  # price units per day
    intercept = mean_y - slope * mean_x  # fitted value at the earliest point

    span_days = max(xs)
    predicted_change = slope * span_days
    denom = intercept if intercept else mean_y
    slope_pct = (predicted_change / denom) if denom else 0.0

    if slope_pct > threshold_pct:
        direction = "rising"
    elif slope_pct < -threshold_pct:
        direction = "falling"
    else:
        direction = "stable"
    return (direction, float(slope_pct))
