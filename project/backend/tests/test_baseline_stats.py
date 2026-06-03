"""feature-001 story-001: pure statistical core (Tukey-trimmed median + IQR + stats).

TDD: these tests are written FIRST and assert the reimplemented bullseye-app
sold-comps PATTERN (Tukey IQR-fence trim over a rolling window) on hand-verified
fixtures. The module under test must be pure — no DB / eBay / I/O imports.
"""
import ast
import inspect
from pathlib import Path

import pytest

from app.services.scoring import baseline_stats


def test_module_is_pure_no_db_or_source_imports():
    """The stats core must not import app.db / app.services.ebay / app.services.sources."""
    src = Path(inspect.getfile(baseline_stats)).read_text()
    tree = ast.parse(src)
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(a.name for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module)
    forbidden = ("app.db", "app.services.ebay", "app.services.sources")
    bad = [m for m in imported for f in forbidden if m == f or m.startswith(f + ".")]
    assert not bad, f"baseline_stats must stay pure; forbidden imports: {bad}"


def test_returned_dict_has_exact_engine_shape():
    # 5 identical-ish points well inside any fence; min_points default met.
    points = [100.0, 110.0, 120.0, 130.0, 140.0]
    stats = baseline_stats.compute_baseline(points, min_points=5)
    assert set(stats.keys()) == {
        "median_price", "avg_price", "std_dev", "min_price", "data_points", "q1", "q3",
    }


def test_median_mean_std_min_on_trimmed_set_hand_verified():
    # No outliers here: all seven points survive the Tukey fence.
    # values: 10,12,14,16,18,20,22  -> median 16, mean 16, min 10, n 7
    points = [10.0, 12.0, 14.0, 16.0, 18.0, 20.0, 22.0]
    stats = baseline_stats.compute_baseline(points, min_points=3)
    assert stats["data_points"] == 7
    assert stats["median_price"] == 16.0
    assert stats["avg_price"] == 16.0
    assert stats["min_price"] == 10.0
    # population std_dev of the arithmetic sequence (step 4): sqrt(112/7)*? compute:
    # deviations^2: 36+16+4+0+4+16+36 = 112; /7 = 16; sqrt = 4.0
    assert stats["std_dev"] == pytest.approx(4.0, abs=1e-9)


def test_tukey_trim_removes_high_outlier():
    # A tight cluster around 100 with one absurd 100000 outlier. The outlier must
    # be trimmed so the median/min reflect the cluster, not the outlier.
    cluster = [95.0, 98.0, 100.0, 102.0, 105.0, 99.0, 101.0, 100.0]
    points = cluster + [100000.0]
    stats = baseline_stats.compute_baseline(points, k=1.5, min_points=3)
    # The outlier is dropped: data_points == len(cluster), min stays in-cluster.
    assert stats["data_points"] == len(cluster)
    assert stats["min_price"] == 95.0
    assert stats["median_price"] == pytest.approx(100.0, abs=2.0)


def test_tukey_keeps_in_fence_points():
    # All points inside [Q1-1.5*IQR, Q3+1.5*IQR] are kept (nothing trimmed).
    points = [40.0, 45.0, 50.0, 55.0, 60.0]
    stats = baseline_stats.compute_baseline(points, k=1.5, min_points=3)
    assert stats["data_points"] == 5


def test_insufficiency_guard_returns_empty_when_below_min_points():
    # Two points but min_points=5 -> insufficiency guard -> {} / None.
    assert not baseline_stats.compute_baseline([100.0, 110.0], min_points=5)


def test_insufficiency_after_trim():
    # Start with enough points, but trimming drops below min_points.
    # 5 tight + 1 outlier; after dropping the outlier 5 remain. min_points=6 fails.
    points = [100.0, 101.0, 99.0, 100.0, 102.0, 100000.0]
    assert not baseline_stats.compute_baseline(points, k=1.5, min_points=6)


def test_empty_list_returns_empty():
    assert not baseline_stats.compute_baseline([], min_points=1)


def test_single_point():
    # A single point with min_points=1: median=mean=min=that point, std_dev 0.
    stats = baseline_stats.compute_baseline([42.0], min_points=1)
    assert stats["data_points"] == 1
    assert stats["median_price"] == 42.0
    assert stats["avg_price"] == 42.0
    assert stats["min_price"] == 42.0
    assert stats["std_dev"] == 0.0
    assert stats["q1"] == 42.0
    assert stats["q3"] == 42.0


def test_all_identical_points_std_dev_zero():
    stats = baseline_stats.compute_baseline([50.0] * 8, min_points=3)
    assert stats["data_points"] == 8
    assert stats["std_dev"] == 0.0
    assert stats["median_price"] == 50.0


def test_min_points_threshold_is_a_parameter_not_hardcoded():
    # Same 4 points: passes when min_points=4, fails when min_points=5.
    pts = [10.0, 20.0, 30.0, 40.0]
    assert baseline_stats.compute_baseline(pts, min_points=4)
    assert not baseline_stats.compute_baseline(pts, min_points=5)


def test_trim_factor_k_is_a_parameter():
    # A moderate outlier survives a generous k but is trimmed by a tight k.
    points = [100.0, 101.0, 99.0, 100.0, 102.0, 130.0]
    loose = baseline_stats.compute_baseline(points, k=5.0, min_points=3)
    tight = baseline_stats.compute_baseline(points, k=0.5, min_points=3)
    assert loose["data_points"] >= tight["data_points"]
