from pydantic import BaseModel
from typing import Optional


class ScoreBreakdown(BaseModel):
    overall_score: int
    deal_score: int
    confidence: float
    classification: str
    price_zscore: Optional[float] = None
    vs_median_pct: Optional[float] = None
    vs_lowest_pct: Optional[float] = None
    est_fair_value: Optional[float] = None
    scam_warning: Optional[str] = None


class DealListResponse(BaseModel):
    deals: list[dict]
    total: int
    page: int
    per_page: int
