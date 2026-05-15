# PHASE 04 — Deal Scoring Engine

## Objective
Build the rules-based deal scoring engine that evaluates listings against historical pricing data and assigns deal scores (0-100) with confidence ratings.

---

## Output Location
`/mnt/agents/output/hardware-deal-tracker/project/backend/app/services/scoring/`

---

## Dependencies
- Phase 1 (database schema) merged to `main`
- Phase 3 (eBay ingestion) recommended but not strictly required
- Branch from: `main`

---

## Research Context

The scoring algorithm is based on a **hybrid statistical approach** (Z-Score + Isolation Forest + DBSCAN voting), which research shows achieves **97.1% precision** for e-commerce price anomaly detection.

**Reference pricing benchmarks** (used for initial scoring when no history exists):

| Item | Median Used Price | "Good Deal" Threshold |
|------|-------------------|----------------------|
| AMD EPYC 7F72 | $340 | Under $255 (25% below) |
| Samsung 64GB ECC | $150 | Under $115 (25% below) |
| Supermicro H12SSL-CT | $700 | Under $490 (30% below) |
| NVIDIA T4 | $200 | Under $150 (25% below) |

---

## Tasks

### Task 1: Historical Price Analytics (`backend/app/services/scoring/historical.py`)

```python
from datetime import datetime, timedelta
from typing import Optional, List
from statistics import median, stdev, mean
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from app.models.price_history import PriceHistory
from app.models.listing import Listing

class HistoricalPriceAnalyzer:
    """Calculate historical price statistics for deal scoring."""
    
    async def get_stats(
        self,
        db: AsyncSession,
        tracked_item_id: int,
        days: int = 30
    ) -> dict:
        since = datetime.utcnow() - timedelta(days=days)
        
        result = await db.execute(
            select(PriceHistory)
            .where(
                and_(
                    PriceHistory.tracked_item_id == tracked_item_id,
                    PriceHistory.timestamp >= since
                )
            )
            .order_by(PriceHistory.timestamp.desc())
        )
        history = result.scalars().all()
        
        if not history:
            return self._empty_stats(tracked_item_id, days)
        
        prices = [float(h.total_price) for h in history]
        
        stats = {
            "tracked_item_id": tracked_item_id,
            "data_points": len(prices),
            "min_price": min(prices),
            "max_price": max(prices),
            "avg_price": round(mean(prices), 2),
            "median_price": round(median(prices), 2),
        }
        
        if len(prices) > 1:
            try:
                stats["std_dev"] = round(stdev(prices), 2)
            except:
                stats["std_dev"] = 0
        else:
            stats["std_dev"] = 0
        
        # Volatility = std_dev / median as percentage
        stats["volatility"] = round(stats["std_dev"] / stats["median_price"] * 100, 2) if stats["median_price"] > 0 else 0
        
        return stats
    
    async def get_multi_period_stats(self, db: AsyncSession, tracked_item_id: int) -> dict:
        stats_7d = await self.get_stats(db, tracked_item_id, 7)
        stats_30d = await self.get_stats(db, tracked_item_id, 30)
        stats_90d = await self.get_stats(db, tracked_item_id, 90)
        
        return {
            "median_7d": stats_7d.get("median_price"),
            "median_30d": stats_30d.get("median_price"),
            "median_90d": stats_90d.get("median_price"),
            "lowest_30d": stats_30d.get("min_price"),
            "highest_30d": stats_30d.get("max_price"),
            "volatility_30d": stats_30d.get("volatility"),
            "total_listings_30d": stats_30d.get("data_points", 0),
        }
    
    def _empty_stats(self, tracked_item_id: int, days: int) -> dict:
        return {
            "tracked_item_id": tracked_item_id,
            "data_points": 0,
            "min_price": None,
            "max_price": None,
            "avg_price": None,
            "median_price": None,
            "std_dev": None,
            "volatility": None,
        }
    
    async def record_price(self, db: AsyncSession, listing_id: int, tracked_item_id: int, price: float, shipping: float = 0):
        history = PriceHistory(
            listing_id=listing_id,
            tracked_item_id=tracked_item_id,
            observed_price=price,
            shipping=shipping,
            total_price=price + shipping
        )
        db.add(history)
```

### Task 2: Deal Scoring Engine (`backend/app/services/scoring/engine.py`)

```python
from datetime import datetime
from typing import Optional, Dict
from app.models.listing import Listing
from app.services.scoring.historical import HistoricalPriceAnalyzer

class DealScoringEngine:
    """Rules-based deal scoring with hybrid statistical components."""
    
    # Fallback price benchmarks for items with no history
    BENCHMARK_PRICES = {
        "epyc 7f72": 340.0, "epyc 7443": 450.0, "epyc 7452": 400.0, "epyc 7543": 550.0,
        "xeon gold 6240": 200.0, "xeon gold 6258r": 350.0,
        "h12ssl": 700.0, "romed8": 650.0, "mz32": 600.0,
        "rtx pro 4000": 900.0, "rtx 6000 ada": 3000.0, "l4": 900.0, "t4": 200.0,
        "m393a8g40mb2": 150.0, "m393a8g40ab2": 160.0, "mta36asf8g72pz": 140.0,
        "hmaa8gr7ajr4n": 140.0,
        "p5510": 100.0, "pm9a3": 100.0,
        "connectx-4": 40.0, "connectx-5": 60.0,
        "rm52": 380.0,
    }
    
    def __init__(self):
        self.historical = HistoricalPriceAnalyzer()
    
    def get_benchmark_price(self, keywords: str) -> Optional[float]:
        keyword_lower = keywords.lower()
        for key, price in self.BENCHMARK_PRICES.items():
            if key in keyword_lower:
                return price
        return None
    
    def calculate_z_score(self, price: float, mean_price: float, std_dev: float) -> float:
        if std_dev == 0:
            return 0.0
        return (price - mean_price) / std_dev
    
    def score_price_zscore(self, z_score: float) -> int:
        """Lower price = higher score. Maps z-score to 0-100."""
        if z_score <= -2.0:
            return 100
        elif z_score <= -1.5:
            return 85
        elif z_score <= -1.0:
            return 70
        elif z_score <= -0.5:
            return 50
        elif z_score <= 0:
            return 30
        elif z_score <= 0.5:
            return 15
        else:
            return max(0, 30 - int(z_score * 20))
    
    def score_historical_discount(self, price: float, median_price: float) -> int:
        """Score based on discount vs median."""
        if median_price <= 0:
            return 50
        discount_pct = (median_price - price) / median_price
        if discount_pct >= 0.50:
            return 100
        elif discount_pct >= 0.30:
            return 70 + int((discount_pct - 0.30) / 0.20 * 30)
        elif discount_pct >= 0.15:
            return 40 + int((discount_pct - 0.15) / 0.15 * 30)
        elif discount_pct >= 0:
            return 20 + int(discount_pct / 0.15 * 20)
        else:
            return max(0, 20 + int(discount_pct * 100))
    
    def score_seller_quality(self, feedback_score: int, positive_pct: float) -> int:
        if feedback_score >= 1000 and positive_pct >= 99.0:
            return 100
        elif feedback_score >= 500 and positive_pct >= 98.0:
            return 90
        elif feedback_score >= 100 and positive_pct >= 97.0:
            return 75
        elif feedback_score >= 50 and positive_pct >= 95.0:
            return 60
        elif feedback_score >= 10:
            return 40
        elif feedback_score > 0:
            return 25
        else:
            return 15  # Unknown seller
    
    def score_listing_quality(self, title: str, condition: Optional[str]) -> int:
        score = 80  # Base score
        title_lower = title.lower()
        
        # Penalties
        penalties = {
            "for dell only": 30, "for hp only": 30, "for ibm only": 30,
            "smartmemory only": 25, "untested": 20, "as-is": 25,
            "for parts": 40, "not working": 40,
            "desktop memory": 30, "udimm": 25,
            "mixed lot": 20, "4rx4": 10,
        }
        
        for phrase, penalty in penalties.items():
            if phrase in title_lower:
                score -= penalty
        
        # Condition adjustments
        if condition:
            condition_scores = {
                "new": 20, "new other": 15, "seller refurbished": 5,
                "used": 0, "very good": 5, "good": 0,
                "for parts or not working": -30,
            }
            score += condition_scores.get(condition.lower(), 0)
        
        return max(0, min(100, score))
    
    def score_market_timing(self, historical_stats: dict) -> int:
        volatility = historical_stats.get("volatility", 0)
        if not volatility:
            return 50
        if volatility > 30:
            return 80  # High volatility = potential deals
        elif volatility > 15:
            return 65
        elif volatility > 5:
            return 50
        else:
            return 40  # Stable market
    
    def calculate_overall_score(
        self,
        listing: Listing,
        historical_stats: dict,
        benchmark_price: Optional[float] = None
    ) -> dict:
        total_price = float(listing.price) + float(listing.shipping)
        median_price = historical_stats.get("median_price")
        mean_price = historical_stats.get("avg_price")
        std_dev = historical_stats.get("std_dev", 0)
        
        # Use benchmark if no history
        if median_price is None and benchmark_price:
            median_price = benchmark_price
            mean_price = benchmark_price
            std_dev = benchmark_price * 0.15  # Assume 15% std dev
        elif median_price is None:
            median_price = total_price
            mean_price = total_price
            std_dev = 0
        
        # Calculate components
        z_score = self.calculate_z_score(total_price, mean_price or median_price, std_dev or 1)
        
        zscore_score = self.score_price_zscore(z_score)
        discount_score = self.score_historical_discount(total_price, median_price)
        seller_score = self.score_seller_quality(listing.seller_feedback, float(listing.seller_positive_pct))
        quality_score = self.score_listing_quality(listing.title, listing.condition)
        timing_score = self.score_market_timing(historical_stats)
        
        # Bulk discount
        bulk_score = 50
        if listing.quantity > 1:
            per_unit = total_price / listing.quantity
            discount = (median_price - per_unit) / median_price if median_price > 0 else 0
            bulk_score = min(100, max(0, int(discount * 150)))
        
        # Weighted average
        overall = round(
            zscore_score * 0.30 +
            discount_score * 0.25 +
            seller_score * 0.15 +
            quality_score * 0.15 +
            timing_score * 0.10 +
            bulk_score * 0.05
        )
        
        # Deal score (focused on value)
        deal_score = round(
            zscore_score * 0.40 +
            discount_score * 0.35 +
            bulk_score * 0.15 +
            seller_score * 0.10
        )
        
        # Confidence based on data availability
        data_points = historical_stats.get("data_points", 0)
        if data_points >= 50:
            confidence = 0.95
        elif data_points >= 20:
            confidence = 0.80
        elif data_points >= 5:
            confidence = 0.60
        elif benchmark_price:
            confidence = 0.45
        else:
            confidence = 0.30
        
        # Classification
        if overall >= 85:
            classification = "hot_deal"
        elif overall >= 70:
            classification = "great_deal"
        elif overall >= 50:
            classification = "good_deal"
        elif overall >= 30:
            classification = "fair_deal"
        else:
            classification = "poor_deal"
        
        vs_median = (median_price - total_price) / median_price if median_price > 0 else 0
        lowest = historical_stats.get("min_price")
        vs_lowest = (lowest - total_price) / lowest if lowest and lowest > 0 else 0
        
        return {
            "overall_score": min(100, max(0, overall)),
            "deal_score": min(100, max(0, deal_score)),
            "confidence": round(confidence, 2),
            "classification": classification,
            "price_zscore": round(z_score, 4),
            "vs_median_pct": round(vs_median, 4),
            "vs_lowest_pct": round(vs_lowest, 4),
            "est_fair_value": round(median_price, 2),
            "breakdown": {
                "price_zscore": {"score": zscore_score, "weight": 0.30},
                "historical_discount": {"score": discount_score, "weight": 0.25},
                "seller_quality": {"score": seller_score, "weight": 0.15},
                "listing_quality": {"score": quality_score, "weight": 0.15},
                "market_timing": {"score": timing_score, "weight": 0.10},
                "bulk_discount": {"score": bulk_score, "weight": 0.05},
            }
        }
```

### Task 3: Scoring Service (`backend/app/services/scoring/__init__.py`)

```python
from app.services.scoring.engine import DealScoringEngine
from app.services.scoring.historical import HistoricalPriceAnalyzer

__all__ = ["DealScoringEngine", "HistoricalPriceAnalyzer"]
```

### Task 4: API Endpoints for Scoring

**`backend/app/api/v1/endpoints/deals.py`** — Replace stub with full implementation:

```python
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, and_
from typing import Optional
from app.api.deps import get_db, get_current_user
from app.models.listing import Listing
from app.models.listing_score import ListingScore
from app.models.tracked_item import TrackedItem
from app.services.scoring import DealScoringEngine
from app.services.scoring.historical import HistoricalPriceAnalyzer
from app.schemas.deal import DealListResponse, DealResponse, ScoreBreakdown

router = APIRouter(prefix="/deals", tags=["deals"])

@router.get("")
async def list_deals(
    min_score: int = Query(50, ge=0, le=100),
    max_score: int = Query(100, ge=0, le=100),
    item_id: Optional[int] = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    user = Depends(get_current_user)
):
    query = (
        select(Listing, ListingScore)
        .join(ListingScore, Listing.id == ListingScore.listing_id)
        .where(
            and_(
                ListingScore.overall_score >= min_score,
                ListingScore.overall_score <= max_score
            )
        )
        .order_by(desc(ListingScore.overall_score))
    )
    
    if item_id:
        query = query.where(Listing.tracked_item_id == item_id)
    
    count_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = count_result.scalar()
    
    query = query.offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(query)
    rows = result.all()
    
    deals = []
    for listing, score in rows:
        deals.append({
            **{k: getattr(listing, k) for k in listing.__dict__ if not k.startswith('_')},
            "score": score
        })
    
    return {"deals": deals, "total": total, "page": page, "per_page": per_page}

@router.post("/score/{listing_id}")
async def score_listing(listing_id: int, db: AsyncSession = Depends(get_db), user = Depends(get_current_user)):
    result = await db.execute(select(Listing).where(Listing.id == listing_id))
    listing = result.scalar_one_or_none()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    
    engine = DealScoringEngine()
    analyzer = HistoricalPriceAnalyzer()
    
    # Get historical stats
    stats = await analyzer.get_stats(db, listing.tracked_item_id) if listing.tracked_item_id else {}
    benchmark = None
    if not stats.get("median_price"):
        from sqlalchemy import select
        item_result = await db.execute(select(TrackedItem).where(TrackedItem.id == listing.tracked_item_id))
        item = item_result.scalar_one_or_none()
        if item:
            benchmark = engine.get_benchmark_price(item.keywords)
    
    score_data = engine.calculate_overall_score(listing, stats, benchmark)
    
    # Store score
    score = ListingScore(
        listing_id=listing_id,
        tracked_item_id=listing.tracked_item_id,
        overall_score=score_data["overall_score"],
        deal_score=score_data["deal_score"],
        confidence=score_data["confidence"],
        classification=score_data["classification"],
        price_zscore=score_data["price_zscore"],
        vs_median_pct=score_data["vs_median_pct"],
        vs_lowest_pct=score_data["vs_lowest_pct"],
        est_fair_value=score_data["est_fair_value"]
    )
    db.add(score)
    await db.flush()
    
    return score_data

@router.get("/{deal_id}")
async def get_deal(deal_id: int, db: AsyncSession = Depends(get_db), user = Depends(get_current_user)):
    result = await db.execute(
        select(Listing, ListingScore)
        .join(ListingScore, Listing.id == ListingScore.listing_id)
        .where(Listing.id == deal_id)
    )
    row = result.first()
    if not row:
        raise HTTPException(status_code=404, detail="Deal not found")
    
    listing, score = row
    return {
        **{k: getattr(listing, k) for k in listing.__dict__ if not k.startswith('_')},
        "score": score,
        "score_breakdown": engine.calculate_overall_score(listing, {}).get("breakdown", {})
    }
```

### Task 5: Update History Endpoints

**`backend/app/api/v1/endpoints/history.py`** — Replace stub:

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from datetime import datetime, timedelta
from app.api.deps import get_db, get_current_user
from app.models.price_history import PriceHistory
from app.models.tracked_item import TrackedItem
from app.services.scoring.historical import HistoricalPriceAnalyzer
from app.schemas.price_history import PriceHistoryResponse, PriceDataPoint, PriceStatsResponse

router = APIRouter(prefix="/history", tags=["history"])

@router.get("/{item_id}")
async def get_history(item_id: int, days: int = 30, db: AsyncSession = Depends(get_db), user = Depends(get_current_user)):
    result = await db.execute(select(TrackedItem).where(TrackedItem.id == item_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Item not found")
    
    since = datetime.utcnow() - timedelta(days=days)
    
    # Daily aggregations using PostgreSQL date_trunc
    from sqlalchemy import text
    query = text("""
        SELECT 
            DATE(timestamp) as date,
            AVG(total_price) as avg_price,
            MIN(total_price) as min_price,
            MAX(total_price) as max_price,
            COUNT(*) as count
        FROM price_history
        WHERE tracked_item_id = :item_id AND timestamp >= :since
        GROUP BY DATE(timestamp)
        ORDER BY date DESC
    """)
    
    result = await db.execute(query, {"item_id": item_id, "since": since})
    rows = result.all()
    
    data_points = [
        PriceDataPoint(
            date=str(row.date),
            avg_price=round(float(row.avg_price), 2),
            min_price=round(float(row.min_price), 2),
            max_price=round(float(row.max_price), 2),
            count=row.count
        )
        for row in rows
    ]
    
    return PriceHistoryResponse(tracked_item_id=item_id, data_points=data_points, days=days)

@router.get("/stats/{item_id}")
async def get_stats(item_id: int, db: AsyncSession = Depends(get_db), user = Depends(get_current_user)):
    result = await db.execute(select(TrackedItem).where(TrackedItem.id == item_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Item not found")
    
    analyzer = HistoricalPriceAnalyzer()
    stats = await analyzer.get_multi_period_stats(db, item_id)
    
    # Count active listings
    from sqlalchemy import select, func
    active_result = await db.execute(
        select(func.count()).select_from(
            select(Listing).where(Listing.tracked_item_id == item_id).subquery()
        )
    )
    stats["active_listings"] = active_result.scalar()
    
    return PriceStatsResponse(tracked_item_id=item_id, **stats)
```

### Task 6: Tests

**`backend/tests/test_scoring.py`**:
```python
import pytest
from app.services.scoring.engine import DealScoringEngine
from app.models.listing import Listing
from datetime import datetime

@pytest.fixture
def engine():
    return DealScoringEngine()

@pytest.fixture
def sample_listing():
    return Listing(
        marketplace_id="test_1",
        title="AMD EPYC 7F72 24-Core 3.2GHz Server CPU Processor TESTED",
        price=250.00,
        shipping=9.99,
        seller="test_seller",
        seller_feedback=1500,
        seller_positive_pct=99.2,
        condition="Used",
        url="https://ebay.com/itm/test",
        listing_date=datetime.utcnow(),
        quantity=1
    )

def test_score_price_zscore(engine):
    assert engine.score_price_zscore(-2.5) == 100
    assert engine.score_price_zscore(-1.5) == 85
    assert engine.score_price_zscore(-1.0) == 70
    assert engine.score_price_zscore(0) == 30
    assert engine.score_price_zscore(1.0) == 10

def test_score_historical_discount(engine):
    assert engine.score_historical_discount(150, 300) == 100  # 50% discount
    assert engine.score_historical_discount(210, 300) == 70   # 30% discount
    assert engine.score_historical_discount(255, 300) == 40   # 15% discount

def test_score_seller_quality(engine):
    assert engine.score_seller_quality(1500, 99.5) == 100
    assert engine.score_seller_quality(50, 96.0) == 60
    assert engine.score_seller_quality(0, 100.0) == 15

def test_score_listing_quality(engine):
    assert engine.score_listing_quality("AMD EPYC 7F72 TESTED CPU", "Used") > 70
    assert engine.score_listing_quality("Untested CPU for parts", "For parts or not working") < 50
    assert engine.score_listing_quality("For Dell only memory module", "Used") < 60

def test_calculate_overall_score(engine, sample_listing):
    stats = {"median_price": 350.0, "avg_price": 360.0, "std_dev": 40.0, "min_price": 220.0, "data_points": 25, "volatility": 11.4}
    result = engine.calculate_overall_score(sample_listing, stats)
    
    assert 0 <= result["overall_score"] <= 100
    assert 0 <= result["deal_score"] <= 100
    assert 0 <= result["confidence"] <= 1
    assert result["vs_median_pct"] > 0  # Price below median should be positive
```

---

## Deliverables

- [ ] `app/services/scoring/engine.py` — Deal scoring engine with all 6 components
- [ ] `app/services/scoring/historical.py` — Historical price analytics
- [ ] `app/services/scoring/__init__.py` — Service exports
- [ ] `app/api/v1/endpoints/deals.py` — Updated with full scoring implementation
- [ ] `app/api/v1/endpoints/history.py` — Updated with price history queries
- [ ] `tests/test_scoring.py` — Scoring engine tests with fixtures

## Git
Branch: `phase-04-scoring`
Base: `main` (after Phase 1 merge)
Commit message: `feat(phase-4): deal scoring engine, historical analytics, scoring endpoints`
