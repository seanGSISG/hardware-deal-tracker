
from pydantic import BaseModel


class ScoreBreakdown(BaseModel):
    overall_score: int
    deal_score: int
    confidence: float
    classification: str
    price_zscore: float | None = None
    vs_median_pct: float | None = None
    vs_lowest_pct: float | None = None
    est_fair_value: float | None = None
    scam_warning: str | None = None


class DealListResponse(BaseModel):
    deals: list[dict]
    total: int
    page: int
    per_page: int
