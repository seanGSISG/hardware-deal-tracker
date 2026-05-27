from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class TrackedItemBase(BaseModel):
    name: str
    keywords: str
    sku: Optional[str] = None
    mpn: Optional[str] = None
    category_id: Optional[str] = None
    marketplace: str = "ebay"
    target_price: Optional[float] = None
    alert_threshold: float = 0.20
    min_deal_score: int = 50
    is_enabled: bool = True
    search_interval: int = 600


class TrackedItemCreate(TrackedItemBase):
    scam_floor: Optional[float] = None
    benchmark_median: Optional[float] = None
    notes: Optional[str] = None


class TrackedItemUpdate(BaseModel):
    name: Optional[str] = None
    keywords: Optional[str] = None
    sku: Optional[str] = None
    mpn: Optional[str] = None
    target_price: Optional[float] = None
    alert_threshold: Optional[float] = None
    min_deal_score: Optional[int] = None
    is_enabled: Optional[bool] = None
    search_interval: Optional[int] = None
    scam_floor: Optional[float] = None
    benchmark_median: Optional[float] = None
    notes: Optional[str] = None


class TrackedItemResponse(TrackedItemBase):
    id: int
    created_at: datetime
    updated_at: datetime
    last_searched: Optional[datetime] = None
    scam_floor: Optional[float] = None
    benchmark_median: Optional[float] = None
    notes: Optional[str] = None
    priority_tier: str
    latest_image_url: Optional[str] = None

    class Config:
        from_attributes = True


class TrackedItemStats(BaseModel):
    total_items: int
    enabled_items: int
    p0_count: int
    p1_count: int
    p2_count: int
    p3_count: int
    estimated_daily_calls: int
