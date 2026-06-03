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
