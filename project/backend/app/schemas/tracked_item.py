from datetime import datetime

from pydantic import BaseModel, ConfigDict, computed_field


class TrackedItemBase(BaseModel):
    name: str
    keywords: str
    sku: str | None = None
    mpn: str | None = None
    category_id: str | None = None
    marketplace: str = "ebay"
    target_price: float | None = None
    alert_threshold: float = 0.20
    min_deal_score: int = 50
    is_enabled: bool = True
    search_interval: int = 600


class TrackedItemCreate(TrackedItemBase):
    scam_floor: float | None = None
    benchmark_median: float | None = None
    notes: str | None = None


class TrackedItemUpdate(BaseModel):
    name: str | None = None
    keywords: str | None = None
    sku: str | None = None
    mpn: str | None = None
    target_price: float | None = None
    alert_threshold: float | None = None
    min_deal_score: int | None = None
    is_enabled: bool | None = None
    search_interval: int | None = None
    scam_floor: float | None = None
    benchmark_median: float | None = None
    notes: str | None = None


class TrackedItemResponse(TrackedItemBase):
    id: int
    created_at: datetime
    updated_at: datetime
    last_searched: datetime | None = None
    scam_floor: float | None = None
    benchmark_median: float | None = None
    notes: str | None = None
    priority_tier: str
    latest_image_url: str | None = None

    class Config:
        from_attributes = True


class TrackedItemListEntry(BaseModel):
    """A single row in the GET /items listing.

    priority_tier is derived from search_interval by a Pydantic v2 computed_field,
    so the tier is never stored or hand-assembled — the schema is the single source
    of truth for the interval -> tier mapping in API responses.
    """
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    keywords: str
    sku: str | None = None
    mpn: str | None = None
    category_id: str | None = None
    marketplace: str = "ebay"
    target_price: float | None = None
    alert_threshold: float = 0.20
    min_deal_score: int = 50
    is_enabled: bool = True
    search_interval: int = 600
    scam_floor: float | None = None
    benchmark_median: float | None = None
    notes: str | None = None
    created_at: datetime
    updated_at: datetime
    last_searched: datetime | None = None
    latest_image_url: str | None = None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def priority_tier(self) -> str:
        if self.search_interval <= 360:
            return "P0"
        if self.search_interval <= 600:
            return "P1"
        if self.search_interval <= 1200:
            return "P2"
        return "P3"


class TrackedItemListResponse(BaseModel):
    items: list[TrackedItemListEntry]
    total: int
    page: int
    per_page: int


class TrackedItemStats(BaseModel):
    total_items: int
    enabled_items: int
    p0_count: int
    p1_count: int
    p2_count: int
    p3_count: int
    estimated_daily_calls: int
