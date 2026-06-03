"""T1.6 smoke suite — fast end-to-end sanity checks over the live ASGI app.

Complements the existing poller/scheduler/search tests with the three highest-value
smoke paths the plan calls out: health, the real auth round-trip, and the scoring
engine over known inputs mapped to expected score buckets. No network is hit (mock
eBay client + in-memory SQLite from conftest).
"""
from app.core.config import settings
from app.models.listing import Listing
from app.services.scoring.engine import DealScoringEngine


async def test_health(client):
    """GET /api/v1/health returns a healthy payload."""
    resp = await client.get("/api/v1/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "healthy"
    assert "version" in body


async def test_auth_register_login_and_protected_route(unauth_client, monkeypatch):
    """Full auth round-trip: register -> JWT -> use bearer token on a protected route."""
    # feature-003 gates registration behind ALLOW_REGISTRATION (default False);
    # enable it for this self-registration smoke path.
    monkeypatch.setattr(settings, "ALLOW_REGISTRATION", True)
    register = await unauth_client.post(
        "/api/v1/auth/register",
        json={"username": "smokeuser", "email": "smoke@example.com", "password": "supersecret123"},
    )
    assert register.status_code == 200
    reg_token = register.json()["access_token"]
    assert reg_token

    # The protected /items route must reject an unauthenticated request...
    unauth = await unauth_client.get("/api/v1/items")
    assert unauth.status_code in (401, 403)

    # ...and accept a freshly minted login token.
    login = await unauth_client.post(
        "/api/v1/auth/login",
        json={"username": "smokeuser", "password": "supersecret123"},
    )
    assert login.status_code == 200
    token = login.json()["access_token"]
    assert token

    items = await unauth_client.get(
        "/api/v1/items", headers={"Authorization": f"Bearer {token}"}
    )
    assert items.status_code == 200
    body = items.json()
    assert "items" in body
    assert "total" in body


def _listing(price, *, shipping=0, condition="Used", feedback=1000, positive=99.5,
             title="NVIDIA RTX 6000 Ada 48GB", quantity=1):
    """A plain Listing instance (not persisted) for scoring-engine unit checks."""
    return Listing(
        marketplace_id="x",
        title=title,
        price=price,
        shipping=shipping,
        seller="s",
        seller_feedback=feedback,
        seller_positive_pct=positive,
        condition=condition,
        url="https://www.ebay.com/itm/x",
        quantity=quantity,
    )


class _Catalog:
    def __init__(self, benchmark_median, scam_floor=0):
        self.benchmark_median = benchmark_median
        self.scam_floor = scam_floor


async def test_scoring_deep_discount_is_hot_deal():
    """A price far below the benchmark from a strong seller lands in the top bucket."""
    engine = DealScoringEngine()
    result = engine.calculate_overall_score(
        _listing(2000), historical_stats={}, catalog_item=_Catalog(benchmark_median=4800)
    )
    assert result["classification"] in ("hot_deal", "great_deal")
    assert result["overall_score"] >= 70
    assert result["scam_warning"] is None


async def test_scoring_at_benchmark_is_middling():
    """A price at the benchmark is a fair/good (not hot) deal."""
    engine = DealScoringEngine()
    result = engine.calculate_overall_score(
        _listing(4800), historical_stats={}, catalog_item=_Catalog(benchmark_median=4800)
    )
    assert 0 <= result["overall_score"] <= 100
    assert result["classification"] in ("fair_deal", "good_deal", "poor_deal")
    assert result["overall_score"] < 85


async def test_scoring_below_scam_floor_flags_suspicious():
    """A price under the scam floor is capped and classified suspicious."""
    engine = DealScoringEngine()
    result = engine.calculate_overall_score(
        _listing(500), historical_stats={}, catalog_item=_Catalog(benchmark_median=4800, scam_floor=3500)
    )
    assert result["scam_warning"] is not None
    assert result["classification"] == "suspicious"
    assert result["overall_score"] <= 30
