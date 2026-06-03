"""Observability — Prometheus /metrics exporter + domain metrics.

The app must expose a /metrics endpoint and a set of domain metrics the Grafana
dashboard depends on: poll cycles, listings ingested, scoring runs, rate-budget
burn (calls_today/remaining/utilization), eBay errors/429s, and scheduler tick
duration.
"""
import app.core.metrics as m


async def test_metrics_endpoint_exposes_prometheus_text(client):
    resp = await client.get("/metrics")
    assert resp.status_code == 200
    # Prometheus exposition format / content type.
    assert "text/plain" in resp.headers["content-type"]
    body = resp.text
    assert "# HELP" in body or "# TYPE" in body


def test_domain_metrics_are_defined():
    # Counters / histograms / gauges the dashboard queries.
    for name in (
        "POLL_CYCLES",
        "LISTINGS_INGESTED",
        "SCORING_RUNS",
        "EBAY_ERRORS",
        "EBAY_RATE_LIMITED",
        "POLL_TICK_DURATION",
        "RATE_BUDGET_CALLS_TODAY",
        "RATE_BUDGET_REMAINING",
        "RATE_BUDGET_UTILIZATION",
    ):
        assert hasattr(m, name), f"missing metric {name}"


def test_counters_increment_and_render():
    before = _counter_value("hdt_listings_ingested_total")
    m.LISTINGS_INGESTED.inc(3)
    after = _counter_value("hdt_listings_ingested_total")
    assert after == before + 3


def test_rate_budget_gauges_settable():
    m.RATE_BUDGET_CALLS_TODAY.set(1234)
    m.RATE_BUDGET_REMAINING.set(3766)
    m.RATE_BUDGET_UTILIZATION.set(24.7)
    assert _gauge_value("hdt_rate_budget_calls_today") == 1234
    assert _gauge_value("hdt_rate_budget_remaining") == 3766
    assert _gauge_value("hdt_rate_budget_utilization_pct") == 24.7


def _counter_value(name: str) -> float:
    from prometheus_client import REGISTRY

    val = REGISTRY.get_sample_value(name)
    return val if val is not None else 0.0


def _gauge_value(name: str) -> float:
    from prometheus_client import REGISTRY

    return REGISTRY.get_sample_value(name)
