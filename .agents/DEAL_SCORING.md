# Deal Scoring Guide

> The 6-component weighted deal scoring algorithm. Read this when modifying scoring, adding components, or debugging deal rankings.

---

## Overview

Each new listing gets a score from **0 to 100** based on 6 weighted components. Scores are persisted in `listing_scores` table and used to rank deals and trigger alerts.

```
Total Score = z_score_component    × 0.30
            + discount_component   × 0.25
            + seller_component     × 0.15
            + quality_component    × 0.15
            + timing_component     × 0.10
            + bulk_component       × 0.05
```

**If price < scam_floor: total_score is capped at 30 and `is_scam_flagged = true`**

---

## Scoring Engine (`services/scoring/engine.py`)

### Entry Point

```python
from app.services.scoring.engine import DealScoringEngine

scorer = DealScoringEngine()
score_result = await scorer.score(listing, tracked_item, price_history)
# Returns: ScoreBreakdown dataclass
```

### ScoreBreakdown Structure

```python
@dataclass
class ScoreBreakdown:
    total_score: float              # 0-100 (capped at 30 if scam)
    z_score_component: float        # 0-100
    discount_component: float       # 0-100
    seller_component: float         # 0-100
    quality_component: float        # 0-100
    timing_component: float         # 0-100
    bulk_component: float           # 0-100
    is_scam_flagged: bool
    scam_floor_hit: Decimal | None
    scoring_version: str            # e.g. "1.0"
```

---

## Component Details

### 1. Z-Score Component (30%)

How far below the moving average this price is. Uses statistical Z-score.

```
z_score = (benchmark_median - listing_price) / price_std_dev
z_score_component = clamp(z_score × 20 + 50, 0, 100)
```

- Negative Z-score (price above average) → lower score
- Positive Z-score (price below average) → higher score
- `price_std_dev` comes from `price_history` table (last 30 days)
- If no history, uses `benchmark_median × 0.15` as estimate

### 2. Discount Component (25%)

Percentage below the benchmark median price.

```
discount_ratio = (benchmark_median - listing_price) / benchmark_median
discount_component = clamp(discount_ratio × 100 × 1.5, 0, 100)
```

- 0% discount = 0 points
- 33% discount = 50 points
- 66% discount = 100 points
- Multiplied by 1.5x to reward deep discounts

### 3. Seller Component (15%)

Composite of seller reputation signals.

```
seller_component = (
    seller_rating_pct × 0.40 +        # % positive feedback (0-100)
    feedback_score_norm × 0.35 +      # Normalized feedback count (0-100)
    top_rated_bonus × 0.25            # 100 if top-rated, 50 otherwise
)
```

- New sellers (0 feedback) get 25 points minimum
- Sellers with >10,000 feedback cap at 100 for feedback score
- Top-rated sellers get a 25% bonus weight

### 4. Quality Component (15%)

Based on item condition.

| Condition | Score |
|-----------|-------|
| New / Brand New / Sealed | 100 |
| Open Box | 85 |
| Manufacturer Refurbished | 75 |
| Seller Refurbished | 60 |
| Used (Good) | 50 |
| Used (Fair) | 35 |
| For Parts / Not Working | 10 |

If condition is unparseable, defaults to 50.

### 5. Timing Component (10%)

Urgency — how quickly you need to act.

```
# For auctions
hours_remaining = (ends_at - now).total_hours
if hours_remaining < 1:     timing_component = 100
elif hours_remaining < 6:   timing_component = 80
elif hours_remaining < 24:  timing_component = 60
elif hours_remaining < 72:  timing_component = 40
else:                       timing_component = 20

# For Buy-It-Now
timing_component = 50  # Neutral
```

### 6. Bulk Component (5%)

Bonus for multi-quantity listings.

```
if quantity >= 10:  bulk_component = 100
elif quantity >= 5: bulk_component = 75
elif quantity >= 2: bulk_component = 50
else:               bulk_component = 25
```

---

## Scam Floor Detection

Before scoring, check if listing price < catalog `scam_floor`:

```python
if listing.price < tracked_item.scam_floor:
    total_score = min(raw_score, 30)  # Cap at 30
    is_scam_flagged = True
    scam_floor_hit = tracked_item.scam_floor
```

This prevents "too good to be true" listings from getting high scores. The listing still appears in results (with a warning badge) so users can review it.

---

## Score Persistence

Scores are saved to `listing_scores` table immediately after scoring. One score record per listing.

The `scoring_version` field allows for algorithm versioning. If you change the scoring formula, increment the version so historical scores can be differentiated.

---

## Alert Thresholds

Alerts are triggered when `total_score ≥ min_score_threshold` (from user's `notification_settings`, default 70):

| Score Range | Classification | Action |
|-------------|----------------|--------|
| 90-100 | Exceptional | Immediate alert + highlight |
| 75-89 | Great | Standard alert |
| 60-74 | Good | Logged, no alert unless threshold lowered |
| 30-59 | Average | Silent |
| 0-29 | Below average or Scam | Flagged if scam |

---

## Modifying the Scoring Algorithm

### Change Weights

Edit `WEIGHTS` dict in `engine.py`:

```python
WEIGHTS = {
    "z_score": 0.30,
    "discount": 0.25,
    "seller": 0.15,
    "quality": 0.15,
    "timing": 0.10,
    "bulk": 0.05,
}
# Must sum to 1.0
```

### Add a New Component

1. Add component calculation method to `DealScoringEngine`
2. Add weight to `WEIGHTS` dict
3. Add field to `ScoreBreakdown` dataclass
4. Add column to `listing_scores` model + migration
5. Increment `SCORING_VERSION`
6. Update tests in `tests/test_scoring.py`

### Change Scam Floor Behavior

Scam floors are defined per-item in `catalog.py`. To change the cap:
1. Edit `SCAM_SCORE_CAP` constant in `engine.py`
2. Update `is_scam_flagged` logic if needed

---

## Testing Scores

```python
# tests/test_scoring.py
async def test_great_deal_scores_high(mock_scorer, sample_listing):
    sample_listing.price = Decimal("100.00")  # 50% below median
    result = await mock_scorer.score(sample_listing)
    assert result.total_score >= 75

async def test_scam_gets_capped(mock_scorer, sample_listing):
    sample_listing.price = Decimal("1.00")  # Way below scam_floor
    result = await mock_scorer.score(sample_listing)
    assert result.total_score <= 30
    assert result.is_scam_flagged is True
```
