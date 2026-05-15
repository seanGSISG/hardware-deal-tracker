# PHASE 03 — eBay Marketplace Ingestion + Catalog + Rate Limiting

## Objective
Build a complete eBay Browse API client with **tiered polling**, **per-item configurable intervals**, **adaptive rate budget management**, **hardware catalog service**, and **scam floor detection**. This phase delivers the core data ingestion pipeline with API limit protection at 4 layers.

---

## Output Location
`/mnt/agents/output/hardware-deal-tracker/project/backend/app/services/ebay/`

---

## Dependencies
- Phase 1 (database schema) merged to `main`
- Branch from: `main`

---

## Research Context

- **eBay Finding API decommissioned Feb 2025** — use ONLY Browse API
- **Browse API**: `GET /buy/browse/v1/item_summary/search`
- **Rate limits**: 5,000 calls/day per app, 1,000 OAuth tokens/day (client_credentials)
- **Max results**: 10,000 per query, 200 per page
- **Filters**: `buyingOptions`, `price`, `conditionIds`, `deliveryCountry`
- **Production access requires approval** — mock mode for development

---

## Tasks

### Task 1: eBay OAuth Client (`backend/app/services/ebay/client.py`)

```python
import time
import httpx
from typing import Optional
from app.core.config import settings
import json

class EbayOAuthClient:
    """Manages eBay OAuth tokens with caching."""
    
    TOKEN_URL = "https://api.ebay.com/identity/v1/oauth2/token"
    _access_token: Optional[str] = None
    _token_expires: float = 0
    
    async def get_token(self) -> str:
        if self._access_token and time.time() < self._token_expires - 60:
            return self._access_token
        
        auth = httpx.BasicAuth(settings.EBAY_APP_ID, settings.EBAY_CERT_ID)
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        data = {
            "grant_type": "client_credentials",
            "scope": "https://api.ebay.com/oauth/api_scope https://api.ebay.com/oauth/api_scope/buy.item.bulk"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(self.TOKEN_URL, auth=auth, headers=headers, data=data)
            response.raise_for_status()
            token_data = response.json()
            self._access_token = token_data["access_token"]
            self._token_expires = time.time() + token_data.get("expires_in", 7200)
            return self._access_token

class EbayBrowseClient:
    """eBay Browse API client with rate limiting."""
    
    BASE_URL = "https://api.ebay.com/buy/browse/v1"
    
    def __init__(self):
        self.oauth = EbayOAuthClient()
        self._daily_calls = 0
        self._daily_reset = time.time() + 86400
    
    def _check_rate_limit(self):
        if time.time() > self._daily_reset:
            self._daily_calls = 0
            self._daily_reset = time.time() + 86400
        if self._daily_calls >= 4800:  # Leave 200 buffer
            raise RuntimeError("Daily eBay API rate limit approaching")
    
    async def search(
        self,
        keywords: str,
        category_id: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        buying_options: Optional[list[str]] = None,
        condition_ids: Optional[list[str]] = None,
        limit: int = 200,
        offset: int = 0,
        sort: str = "-itemEndDate"
    ) -> dict:
        self._check_rate_limit()
        
        token = await self.oauth.get_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "X-EBAY-C-MARKETPLACE-ID": "EBAY_US",
            "Content-Type": "application/json"
        }
        
        params = {"q": keywords, "limit": limit, "offset": offset, "sort": sort}
        
        filters = []
        if category_id:
            params["category_ids"] = category_id
        if buying_options:
            filters.append(f"buyingOptions:{{'|'.join(buying_options)}}")
        if condition_ids:
            filters.append(f"conditionIds:{{'|'.join(condition_ids)}}")
        if min_price or max_price:
            price_range = f"[{min_price or ''}..{max_price or ''}]"
            filters.append(f"price:{price_range},priceCurrency:USD")
        filters.append("deliveryCountry:US")
        
        if filters:
            params["filter"] = ",".join(filters)
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{self.BASE_URL}/item_summary/search",
                headers=headers,
                params=params
            )
            self._daily_calls += 1
            response.raise_for_status()
            return response.json()
```

### Task 2: Mock Client (`backend/app/services/ebay/mock.py`)

Create a mock eBay client for development (when `USE_MOCK_EBAY=true`):

```python
import random
from datetime import datetime, timedelta
from typing import Optional

class MockEbayClient:
    """Mock eBay client for development/testing."""
    
    MOCK_SELLERS = ["serverdeals", "techliquidators", "datacenterpulls", "homedata", "enterprisehw"]
    MOCK_CONDITIONS = ["Used", "New", "Seller refurbished", "For parts or not working"]
    
    async def search(self, keywords: str, **kwargs) -> dict:
        count = random.randint(3, 25)
        items = []
        base_price = self._estimate_base_price(keywords)
        
        for i in range(count):
            price_variation = random.uniform(0.5, 1.5)
            price = round(base_price * price_variation, 2)
            shipping = random.choice([0, 0, 9.99, 14.99, 24.99])
            
            items.append({
                "itemId": f"mock_{abs(hash(keywords))}_{i}_{int(datetime.utcnow().timestamp())}",
                "title": self._generate_title(keywords),
                "price": {"value": str(price), "currency": "USD"},
                "shippingOptions": [{"shippingCost": {"value": str(shipping), "currency": "USD"}}],
                "seller": {"username": random.choice(self.MOCK_SELLERS), "feedbackScore": random.randint(50, 5000), "feedbackPercentage": str(round(random.uniform(95.0, 100.0), 1))},
                "condition": random.choice(self.MOCK_CONDITIONS),
                "conditionId": random.choice(["3000", "1000", "2500", "7000"]),
                "itemWebUrl": f"https://www.ebay.com/itm/mock-{i}",
                "image": {"imageUrl": f"https://i.ebayimg.com/mock-{i}.jpg"},
                "buyingOptions": random.choice([["FIXED_PRICE"], ["FIXED_PRICE", "BEST_OFFER"], ["AUCTION"]]),
                "itemEndDate": (datetime.utcnow() + timedelta(days=random.randint(1, 30))).isoformat() + "Z",
                "listingDate": (datetime.utcnow() - timedelta(days=random.randint(0, 7))).isoformat() + "Z",
                "categories": [{"categoryId": "164", "categoryName": "CPUs/Processors"}]
            })
        
        return {"itemSummaries": items, "total": count, "offset": 0, "limit": 200}
    
    def _estimate_base_price(self, keywords: str) -> float:
        keyword_lower = keywords.lower()
        price_map = {
            "epyc 7f72": 350.0, "epyc 7443": 450.0, "epyc 7452": 400.0, "epyc 7543": 550.0,
            "xeon gold 6240": 200.0, "xeon gold 6258r": 350.0,
            "h12ssl": 500.0, "romed8": 600.0, "mz32": 550.0,
            "rtx pro 4000": 900.0, "rtx 6000 ada": 3000.0, "l4": 900.0, "t4": 200.0,
            "m393a8g40mb2": 150.0, "m393a8g40ab2": 160.0, "mta36asf8g72pz": 140.0,
            "hmaa8gr7ajr4n": 140.0,
            "p5510": 100.0, "pm9a3": 100.0, "7450": 90.0,
            "connectx-4": 40.0, "connectx-5": 60.0, "x710": 50.0,
            "rm52": 380.0, "rm44": 300.0,
        }
        for key, price in price_map.items():
            if key in keyword_lower:
                return price
        return 100.0
    
    def _generate_title(self, keywords: str) -> str:
        prefixes = ["", "Genuine ", "OEM ", "TESTED ", "Pull ", "Enterprise ", "Datacenter "]
        suffixes = ["", " - Fast Ship", " - Tested Working", " - FREE SHIPPING", " - Server Pull", " Bulk Lot"]
        return f"{random.choice(prefixes)}{keywords}{random.choice(suffixes)}"
```

### Task 3: Listing Parser (`backend/app/services/ebay/parser.py`)

```python
from datetime import datetime
from typing import Optional
from app.schemas.listing import ListingCreate

class ListingParser:
    """Parse eBay Browse API responses into ListingCreate schemas."""
    
    def parse_item(self, item: dict, tracked_item_id: Optional[int] = None) -> ListingCreate:
        price_data = item.get("price", {})
        price = float(price_data.get("value", 0))
        
        shipping = 0.0
        shipping_options = item.get("shippingOptions", [])
        if shipping_options and shipping_options[0].get("shippingCost"):
            shipping = float(shipping_options[0]["shippingCost"].get("value", 0))
        
        seller_data = item.get("seller", {})
        feedback_score = seller_data.get("feedbackScore", 0) or 0
        feedback_pct_str = seller_data.get("feedbackPercentage", "100")
        try:
            feedback_pct = float(feedback_pct_str)
        except (ValueError, TypeError):
            feedback_pct = 100.0
        
        buying_options = item.get("buyingOptions", ["FIXED_PRICE"])
        if isinstance(buying_options, str):
            buying_options = [buying_options]
        
        listing_date = datetime.utcnow()
        if item.get("listingDate"):
            try:
                listing_date = datetime.fromisoformat(item["listingDate"].replace("Z", "+00:00")).replace(tzinfo=None)
            except (ValueError, TypeError):
                pass
        
        end_date = None
        if item.get("itemEndDate"):
            try:
                end_date = datetime.fromisoformat(item["itemEndDate"].replace("Z", "+00:00")).replace(tzinfo=None)
            except (ValueError, TypeError):
                pass
        
        categories = item.get("categories", [])
        category_id = categories[0].get("categoryId") if categories else None
        
        return ListingCreate(
            marketplace_id=str(item.get("itemId", "")),
            tracked_item_id=tracked_item_id,
            title=item.get("title", ""),
            price=price,
            shipping=shipping,
            seller=seller_data.get("username", "unknown"),
            seller_feedback=feedback_score,
            seller_positive_pct=feedback_pct,
            condition=item.get("condition"),
            condition_id=item.get("conditionId"),
            category_id=category_id,
            url=item.get("itemWebUrl", ""),
            image_url=item.get("image", {}).get("imageUrl") if item.get("image") else None,
            is_auction="AUCTION" in buying_options and "FIXED_PRICE" not in buying_options,
            buying_options=buying_options,
            listing_date=listing_date,
            end_date=end_date,
            raw_data=item
        )
    
    def parse_search_response(self, response: dict, tracked_item_id: Optional[int] = None) -> list[ListingCreate]:
        items = response.get("itemSummaries", [])
        return [self.parse_item(item, tracked_item_id) for item in items]
```

### Task 4: Deduplication Engine (`backend/app/services/ebay/dedup.py`)

```python
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.listing import Listing

class DeduplicationEngine:
    """Prevent duplicate listings from being stored."""
    
    async def is_duplicate(self, db: AsyncSession, marketplace_id: str) -> bool:
        result = await db.execute(select(Listing).where(Listing.marketplace_id == marketplace_id))
        return result.scalar_one_or_none() is not None
    
    async def dedup_batch(self, db: AsyncSession, listings: list) -> tuple[list, int]:
        new_listings = []
        duplicates = 0
        
        for listing in listings:
            exists = await self.is_duplicate(db, listing.marketplace_id)
            if not exists:
                new_listings.append(listing)
            else:
                duplicates += 1
        
        return new_listings, duplicates
```

### Task 5: Rate Budget Manager (`backend/app/services/ebay/rate_budget.py`)

```python
from datetime import datetime, timedelta
from app.core.config import settings

class RateBudgetManager:
    """Tracks and enforces the daily eBay API call budget.
    
    Uses Redis for fast atomic operations. Falls back to in-memory if Redis unavailable.
    Implements 4 protection layers:
    - Layer 1: Per-item intervals (from user config)
    - Layer 2: Global daily counter (Redis)
    - Layer 3: Priority-based skipping when near limit
    - Layer 4: Hard stop when at limit
    """
    
    DAILY_LIMIT = settings.EBAY_DAILY_CALL_LIMIT  # 5000
    BUFFER = settings.EBAY_CALL_BUFFER  # 200
    NEAR_LIMIT = settings.EBAY_NEAR_LIMIT_THRESHOLD  # 4000
    
    # Priority multipliers for scheduling (seconds of artificial delay)
    PRIORITY_DELAY = {"P0": 0, "P1": 10, "P2": 30, "P3": 60}
    
    def __init__(self, redis_client=None):
        self.redis = redis_client
        self._memory_count = 0
        self._memory_date = datetime.utcnow().date()
    
    def _key(self) -> str:
        return f"ebay_calls:{datetime.utcnow().strftime('%Y%m%d')}"
    
    async def get_today_count(self) -> int:
        if self.redis:
            count = await self.redis.get(self._key())
            return int(count) if count else 0
        # In-memory fallback
        if datetime.utcnow().date() != self._memory_date:
            self._memory_count = 0
            self._memory_date = datetime.utcnow().date()
        return self._memory_count
    
    async def record_call(self):
        if self.redis:
            pipe = self.redis.pipeline()
            pipe.incr(self._key())
            pipe.expire(self._key(), 86400)
            await pipe.execute()
        else:
            if datetime.utcnow().date() != self._memory_date:
                self._memory_count = 0
                self._memory_date = datetime.utcnow().date()
            self._memory_count += 1
    
    async def can_search(self, priority: str = "P1") -> bool:
        """Check if we have budget to make a search call."""
        count = await self.get_today_count()
        
        # Layer 4: Hard stop
        if count >= self.DAILY_LIMIT - self.BUFFER:
            return False
        
        # Layer 3: Near limit, skip lower priorities
        if count >= self.NEAR_LIMIT and priority not in ("P0",):
            return False
        
        return True
    
    async def get_budget_status(self) -> dict:
        count = await self.get_today_count()
        remaining = self.DAILY_LIMIT - count
        return {
            "calls_today": count,
            "daily_limit": self.DAILY_LIMIT,
            "remaining": remaining,
            "buffer": self.BUFFER,
            "utilization_pct": round(count / self.DAILY_LIMIT * 100, 1),
            "status": "ok" if remaining > self.BUFFER else "critical" if remaining <= 0 else "warning",
            "searches_possible": remaining - self.BUFFER
        }
    
    def get_priority_for_interval(self, interval: int) -> str:
        """Map interval to priority tier for scheduling."""
        if interval <= 360:
            return "P0"
        elif interval <= 600:
            return "P1"
        elif interval <= 1200:
            return "P2"
        return "P3"
```

### Task 6: Hardware Catalog (`backend/app/services/ebay/catalog.py`)

```python
from typing import List, Optional
from dataclasses import dataclass

@dataclass
class CatalogItem:
    name: str
    keywords: str
    sku: str
    mpn: str
    category_id: str
    target_price: float
    alert_threshold: float
    search_interval: int
    benchmark_median: float
    scam_floor: float  # Minimum price below which listings are flagged as suspicious
    notes: str = ""

class HardwareCatalog:
    """Pre-loaded catalog of common enterprise hardware SKUs with validated pricing.
    Used by the Add Item wizard to auto-populate tracked items."""
    
    ITEMS: List[CatalogItem] = [
        # CPUs
        CatalogItem("AMD EPYC 7F72", "AMD EPYC 7F72 server CPU processor SP3",
            "100-000000336", "7F72", "164", 325.0, 0.15, 300, 375.0, 280.0,
            "Abundant China supply. Make offers at $320-340."),
        
        # Motherboards
        CatalogItem("Supermicro H12SSL-CT", "Supermicro H12SSL-CT motherboard SP3 EPYC",
            "MBD-H12SSL-CT-O", "H12SSL-CT", "1244", 650.0, 0.10, 600, 634.0, 500.0,
            "Pre-owned risen from $620. Watch for open-box at $600-700."),
        CatalogItem("ASRock Rack ROMED8-2T", "ASRock Rack ROMED8-2T motherboard SP3 EPYC",
            "ROMED8-2T", "ROMED8-2T", "1244", 900.0, 0.12, 600, 1003.0, 800.0,
            "New boards $1,000-1,080. Open-box rare at $825."),
        
        # Workstation GPUs
        CatalogItem("NVIDIA RTX PRO 6000 Blackwell 96GB", 
            "NVIDIA RTX PRO 6000 Blackwell Workstation 96GB GPU",
            "900-5G180-2550-000", "RTX PRO 6000", "27386", 6500.0, 0.10, 1200, 7999.0, 7000.0,
            "SCAM WARNING: Listings below $7,000 are confirmed scams. Too new for used market."),
        CatalogItem("NVIDIA RTX 6000 Ada 48GB", "NVIDIA RTX 6000 Ada workstation GPU 48GB",
            "900-5G133-2500-000", "RTX 6000 Ada", "27386", 4200.0, 0.12, 600, 4800.0, 3500.0,
            "Legit used $4,500-5,500. Below $3,500 = scam."),
        CatalogItem("NVIDIA RTX PRO 4000 Blackwell SFF",
            "NVIDIA RTX PRO 4000 Blackwell SFF workstation GPU",
            "900-5G173-2550-000", "RTX PRO 4000", "27386", 1350.0, 0.12, 600, 1700.0, 1400.0,
            "New card, no used market yet. $1,599 retail."),
        
        # Inference GPUs
        CatalogItem("NVIDIA L4 24GB", "NVIDIA L4 24GB GPU inference accelerator",
            "900-2G193-0000-000", "L4", "27386", 2600.0, 0.15, 600, 3400.0, 2000.0,
            "Current-gen inference GPU. $2,400+ market floor."),
        CatalogItem("NVIDIA T4 16GB", "NVIDIA T4 16GB GPU inference accelerator",
            "900-2G183-0000-000", "T4", "27386", 450.0, 0.20, 300, 637.0, 250.0,
            "US sellers $565+. China direct $280-420."),
        
        # ECC Memory
        CatalogItem("Samsung 64GB DDR4-2933 ECC M393A8G40MB2-CVF",
            "Samsung M393A8G40MB2-CVF 64GB DDR4 ECC RDIMM server memory",
            "M393A8G40MB2-CVF", "M393A8G40MB2-CVF", "170083", 135.0, 0.20, 300, 240.0, 100.0,
            "DDR4 prices RISING. Buy sooner. Target OBO at 20-30% below BIN."),
        CatalogItem("Samsung 64GB DDR4-3200 ECC M393A8G40AB2-CWE",
            "Samsung M393A8G40AB2-CWE 64GB DDR4 ECC RDIMM server memory",
            "M393A8G40AB2-CWE", "M393A8G40AB2-CWE", "170083", 115.0, 0.20, 300, 145.0, 85.0,
            "Best value. Reddit r/homelabsales lots at $90/unit."),
        CatalogItem("Micron 64GB DDR4-2933 ECC MTA36ASF8G72PZ-2G9",
            "Micron MTA36ASF8G72PZ-2G9 64GB DDR4 ECC RDIMM server memory",
            "MTA36ASF8G72PZ-2G9", "MTA36ASF8G72PZ-2G9", "170083", 125.0, 0.20, 300, 185.0, 100.0,
            "Good availability. $125 via OBO or used pulls."),
        CatalogItem("Hynix 64GB DDR4-2933 ECC HMAA8GR7CJR4N-WM",
            "SK Hynix HMAA8GR7CJR4N-WM 64GB DDR4 ECC RDIMM server memory",
            "HMAA8GR7CJR4N-WM", "HMAA8GR7CJR4N-WM", "170083", 120.0, 0.25, 300, 575.0, 100.0,
            "Expensive on eBay ($400-900 BIN). Watch Walmart/surplus."),
        CatalogItem("Hynix 64GB DDR4-2933 ECC HMAA8GR7AJR4N-WM",
            "SK Hynix HMAA8GR7AJR4N-WM 64GB DDR4 ECC RDIMM server memory",
            "HMAA8GR7AJR4N-WM", "HMAA8GR7AJR4N-WM", "170083", 120.0, 0.25, 300, 310.0, 100.0,
            "eBay $400-800. Walmart pre-owned $119 (sold out)."),
        
        # Chassis / Cooling / PSU
        CatalogItem("SilverStone RM52 5U Rackmount Chassis",
            "SilverStone RM52 5U rackmount chassis server case",
            "SST-RM52", "RM52", "42014", 530.0, 0.10, 1200, 585.0, 450.0,
            "Niche product, no used market. Watch for seasonal sales."),
        CatalogItem("SilverStone RM44 4U Rackmount Chassis",
            "SilverStone RM44 4U rackmount chassis server case",
            "SST-RM44", "RM44", "42014", 360.0, 0.12, 1200, 385.0, 300.0,
            "Less popular than RM52. Better chance of open-box deals."),
        CatalogItem("Alphacool Eisbaer Pro HPE Aurora 360",
            "Alphacool Eisbaer Pro HPE Aurora 360 AIO CPU cooler SP3",
            "1019572", "Eisbaer-Pro-HPE-Aurora-360", "42007", 210.0, 0.15, 1200, 265.0, 180.0,
            "Alphacool suspended US direct. Buy via Titan Rig ($227)."),
        CatalogItem("Corsair HX1500i 2025 ATX 3.1",
            "Corsair HX1500i 2025 ATX 3.1 power supply 1500W",
            "CP-9020309-NA", "HX1500i", "42006", 250.0, 0.15, 1200, 350.0, 170.0,
            "Prices softening. Open-box deals increasing."),
        
        # Networking
        CatalogItem("Mellanox ConnectX-4 25GbE MCX4111A",
            "Mellanox ConnectX-4 25GbE SFP28 network adapter MCX4111A",
            "MCX4111A-ACAT", "ConnectX-4", "51167", 30.0, 0.25, 600, 42.0, 20.0,
            "China sellers $33-40. Core4Solutions $34.95."),
        CatalogItem("Mellanox ConnectX-5 25GbE MCX512A",
            "Mellanox ConnectX-5 25GbE SFP28 network adapter MCX512A",
            "MCX512A-ACAT", "ConnectX-5", "51167", 50.0, 0.20, 600, 65.0, 25.0,
            "EOL Jan 2025 = liquidation inventory."),
        CatalogItem("Mellanox ConnectX-6 100GbE MCX653106A",
            "Mellanox ConnectX-6 100GbE QSFP28 network adapter MCX653106A",
            "MCX653106A-ECAT", "ConnectX-6", "51167", 550.0, 0.15, 600, 649.0, 424.0,
            "100GbE holds value. $500-650 used."),
        
        # U.2 NVMe Storage
        CatalogItem("Intel P5510 1.92TB U.2",
            "Intel P5510 1.92TB U.2 NVMe enterprise SSD",
            "SSDPE2KX019T801", "P5510", "56083", 360.0, 0.15, 600, 400.0, 300.0,
            "Consider older P4510 at $150-250 as budget alternative."),
        CatalogItem("Intel P5510 3.84TB U.2",
            "Intel P5510 3.84TB U.2 NVMe enterprise SSD",
            "SSDPE2KX038T801", "P5510-4T", "56083", 500.0, 0.10, 600, 545.0, 400.0,
            "Best $/TB among P5510 sizes."),
        CatalogItem("Samsung PM9A3 1.92TB U.2",
            "Samsung PM9A3 1.92TB U.2 NVMe enterprise SSD",
            "MZQL21T9HCJR", "PM9A3", "56083", 560.0, 0.10, 600, 607.0, 450.0,
            "Samsung brand premium. Offer 10% below BIN."),
        CatalogItem("Samsung PM9A3 3.84TB U.2",
            "Samsung PM9A3 3.84TB U.2 NVMe enterprise SSD",
            "MZQL23T8HCLS", "PM9A3-4T", "56083", 920.0, 0.10, 600, 1023.0, 750.0,
            "Most expensive U.2 drive. Good performance but costly."),
        CatalogItem("Micron 7450 1.92TB U.2",
            "Micron 7450 1.92TB U.2 NVMe enterprise SSD",
            "MTFDKCB1T9TFS-1BC1ZABYY", "7450", "56083", 440.0, 0.10, 600, 475.0, 350.0,
            "Good availability. Best value current-gen U.2."),
        CatalogItem("Micron 7450 Pro 3.84TB U.2",
            "Micron 7450 Pro 3.84TB U.2 NVMe enterprise SSD",
            "MTFDKCB3T8TFS-1BC15ABYY", "7450-4T", "56083", 620.0, 0.10, 600, 673.0, 500.0,
            "Best $/TB at ~$162/TB. $500 was anomaly listing."),
        
        # HDD 16TB+ (NEW)
        CatalogItem("Seagate Exos X16 16TB",
            "Seagate Exos X16 16TB ST16000NM001G enterprise HDD SATA",
            "ST16000NM001G", "ST16000NM001G", "56083", 230.0, 0.15, 600, 268.0, 180.0,
            "Best all-rounder. 4x RAIDZ2 = 32TB usable ~$920."),
        CatalogItem("Seagate Exos X18 18TB",
            "Seagate Exos X18 18TB ST18000NM000J enterprise HDD SATA",
            "ST18000NM000J", "ST18000NM000J", "56083", 270.0, 0.10, 600, 296.0, 220.0,
            "$16.44/TB. 4x RAIDZ2 = 36TB usable ~$1,080."),
        CatalogItem("WD Ultrastar HC550 16TB",
            "WD Ultrastar HC550 16TB WUH721816ALE6L4 enterprise HDD SATA",
            "WUH721816ALE6L4", "WUH721816ALE6L4", "56083", 265.0, 0.10, 600, 295.0, 200.0,
            "Reliable alternative to Exos. $18.44/TB."),
        CatalogItem("WD Ultrastar HC550 18TB",
            "WD Ultrastar HC550 18TB WUH721818ALE6L4 enterprise HDD SATA",
            "WUH721818ALE6L4", "WUH721818ALE6L4", "56083", 260.0, 0.10, 600, 280.0, 200.0,
            "BEST $/TB at $15.56/TB! 4x RAIDZ2 = 36TB usable ~$1,040. RECOMMENDED."),
        CatalogItem("Toshiba MG08 16TB",
            "Toshiba MG08 16TB MG08ACA16TE enterprise HDD SATA",
            "MG08ACA16TE", "MG08ACA16TE", "56083", 330.0, 0.08, 600, 350.0, 280.0,
            "Higher $/TB ($21.88) but good reliability. Less common on eBay."),
        CatalogItem("Toshiba MG09 18TB",
            "Toshiba MG09 18TB MG09ACA18TE enterprise HDD SATA",
            "MG09ACA18TE", "MG09ACA18TE", "56083", 290.0, 0.08, 600, 310.0, 240.0,
            "$17.22/TB. Good middle ground between Exos and Ultrastar."),
        
        # Accessories
        CatalogItem("GPU Support Bracket Anti-Sag", "GPU support bracket anti sag holder workstation",
            "", "", "42014", 7.0, 0.30, 1200, 10.0, 4.0,
            "Pure commodity. China $4-8. Don't overpay."),
        CatalogItem("SilverStone RM52 Rack Rails", "SilverStone RM52 rack rails mounting kit RMS05-22",
            "RMS05-22", "RMS05-22", "42014", 85.0, 0.15, 1200, 100.0, 70.0,
            "Proprietary, no alternatives. Consider universal rack shelf."),
    ]
    
    @classmethod
    def search(cls, query: str) -> List[CatalogItem]:
        """Fuzzy search catalog items by name, keywords, SKU, or MPN."""
        query_lower = query.lower()
        results = []
        for item in cls.ITEMS:
            if (query_lower in item.name.lower() or 
                query_lower in item.keywords.lower() or
                query_lower in item.sku.lower() or
                query_lower in item.mpn.lower()):
                results.append(item)
        return results
    
    @classmethod
    def get_by_name(cls, name: str) -> Optional[CatalogItem]:
        for item in cls.ITEMS:
            if item.name == name:
                return item
        return None
    
    @classmethod
    def get_categories(cls) -> List[dict]:
        """Return eBay categories for frontend picker."""
        return [
            {"id": "164", "name": "CPUs/Processors"},
            {"id": "1244", "name": "Motherboards"},
            {"id": "27386", "name": "Graphics/Video Cards"},
            {"id": "170083", "name": "Enterprise Memory (RAM)"},
            {"id": "42014", "name": "Computer Cases"},
            {"id": "42006", "name": "Power Supplies"},
            {"id": "42007", "name": "CPU Fans & Heatsinks"},
            {"id": "51167", "name": "Enterprise Networking"},
            {"id": "56083", "name": "Hard Drives (HDD/SSD)"},
        ]
```

### Task 7: Tiered Poller Service (`backend/app/services/ebay/poller.py`)

Replace the existing poller with this tiered version:

```python
import time
from datetime import datetime, timedelta
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from app.core.config import settings
from app.services.ebay.client import EbayBrowseClient
from app.services.ebay.mock import MockEbayClient
from app.services.ebay.parser import ListingParser
from app.services.ebay.dedup import DeduplicationEngine
from app.services.ebay.rate_budget import RateBudgetManager
from app.models.tracked_item import TrackedItem
from app.models.listing import Listing

class EbayPoller:
    """Orchestrates tiered eBay searches with rate budget protection."""
    
    # Preset interval tiers
    PRESETS = {
        "hot": 300,       # 5 min
        "standard": 600,  # 10 min
        "monitor": 1200,  # 20 min
        "passive": 1800,  # 30 min
    }
    
    def __init__(self, redis_client=None):
        if settings.USE_MOCK_EBAY:
            self.client = MockEbayClient()
        else:
            self.client = EbayBrowseClient()
        self.parser = ListingParser()
        self.dedup = DeduplicationEngine()
        self.budget = RateBudgetManager(redis_client)
    
    async def get_items_due(self, db: AsyncSession) -> List[TrackedItem]:
        """Get items that are due for polling, ordered by priority."""
        budget_mgr = self.budget
        
        # Calculate effective next-search time with priority delay
        # P0 (hot): no delay, P1 (standard): +10s, P2 (monitor): +30s, P3 (passive): +60s
        result = await db.execute(
            select(TrackedItem)
            .where(
                and_(
                    TrackedItem.is_enabled == True,
                    TrackedItem.last_searched == None  # Never searched items first
                )
            )
            .order_by(TrackedItem.last_searched.asc())
            .limit(10)
        )
        never_searched = result.scalars().all()
        
        # Then get items past their interval, with priority ordering
        now = datetime.utcnow()
        result = await db.execute(
            select(TrackedItem)
            .where(
                and_(
                    TrackedItem.is_enabled == True,
                    TrackedItem.last_searched != None,
                    TrackedItem.last_searched <= now - TrackedItem.search_interval * text("'1 second'::interval")
                )
            )
            .order_by(
                # Priority ordering: shorter interval = higher priority
                TrackedItem.search_interval.asc(),
                TrackedItem.last_searched.asc()
            )
            .limit(20)
        )
        due_items = result.scalars().all()
        
        return list(never_searched) + list(due_items)
    
    async def search_item(self, db: AsyncSession, item: TrackedItem) -> dict:
        """Search eBay for a single tracked item with rate budget check."""
        start_time = time.time()
        
        # Check rate budget
        priority = self.budget.get_priority_for_interval(item.search_interval)
        can_search = await self.budget.can_search(priority)
        if not can_search:
            return {
                "listings_found": 0, "new_listings": 0, "duplicates_skipped": 0,
                "duration_ms": 0, "skipped": True, "reason": "Rate budget exhausted",
                "priority": priority
            }
        
        try:
            response = await self.client.search(
                keywords=item.keywords,
                category_id=item.category_id,
                buying_options=["FIXED_PRICE", "AUCTION"]
            )
            
            # Record the API call
            await self.budget.record_call()
            
            raw_listings = self.parser.parse_search_response(response, item.id)
            new_listings, duplicates = await self.dedup.dedup_batch(db, raw_listings)
            
            for listing_data in new_listings:
                listing = Listing(**listing_data.model_dump(exclude_unset=True))
                db.add(listing)
            
            item.last_searched = datetime.utcnow()
            await db.flush()
            
            duration = int((time.time() - start_time) * 1000)
            budget_status = await self.budget.get_budget_status()
            
            return {
                "listings_found": len(raw_listings),
                "new_listings": len(new_listings),
                "duplicates_skipped": duplicates,
                "duration_ms": duration,
                "priority": priority,
                "budget": budget_status
            }
        except Exception as e:
            return {
                "listings_found": 0, "new_listings": 0, "duplicates_skipped": 0,
                "duration_ms": 0, "error": str(e), "priority": priority
            }
    
    async def search_all(self, db: AsyncSession) -> dict:
        """Poll all due items in priority order with rate budget protection."""
        items = await self.get_items_due(db)
        
        total_results = {
            "items_due": len(items),
            "items_processed": 0, "items_skipped": 0,
            "total_listings": 0, "total_new": 0,
            "total_duplicates": 0, "errors": [],
            "budget": await self.budget.get_budget_status()
        }
        
        for item in items:
            # Double-check budget before each call
            priority = self.budget.get_priority_for_interval(item.search_interval)
            if not await self.budget.can_search(priority):
                total_results["items_skipped"] += 1
                continue
            
            result = await self.search_item(db, item)
            
            if result.get("skipped"):
                total_results["items_skipped"] += 1
            else:
                total_results["items_processed"] += 1
                total_results["total_listings"] += result["listings_found"]
                total_results["total_new"] += result["new_listings"]
                total_results["total_duplicates"] += result["duplicates_skipped"]
            
            if "error" in result:
                total_results["errors"].append({"item": item.name, "error": result["error"]})
        
        # Final budget status
        total_results["budget"] = await self.budget.get_budget_status()
        return total_results
    
    async def get_budget_status(self) -> dict:
        """Return current API budget status for frontend dashboard."""
        return await self.budget.get_budget_status()
    
    @classmethod
    def get_preset_interval(cls, preset: str) -> int:
        return cls.PRESETS.get(preset, 600)
```

### Task 8: Scam Floor Detection in Scoring

The scoring engine (Phase 4) should check `scam_floor` from the catalog:

```python
# In DealScoringEngine.calculate_overall_score()
# Before scoring, check if price is below scam floor
if catalog_item and catalog_item.scam_floor:
    total_price = float(listing.price) + float(listing.shipping)
    if total_price < catalog_item.scam_floor:
        # Flag as suspicious — reduce score and add warning
        result["scam_warning"] = f"Price ${total_price} is below known scam floor of ${catalog_item.scam_floor}"
        result["overall_score"] = min(result["overall_score"], 30)  # Cap at 30
        result["classification"] = "suspicious"
```

### Task 9: Wire into API Endpoints

Update `backend/app/api/v1/endpoints/search.py`:

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.api.deps import get_db, get_current_user
from app.models.tracked_item import TrackedItem
from app.services.ebay.poller import EbayPoller
from app.services.ebay.catalog import HardwareCatalog
from app.services.ebay.rate_budget import RateBudgetManager

router = APIRouter(prefix="/search", tags=["search"])

@router.post("/trigger/{item_id}")
async def trigger_search(item_id: int, db: AsyncSession = Depends(get_db), user = Depends(get_current_user)):
    result = await db.execute(select(TrackedItem).where(TrackedItem.id == item_id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    poller = EbayPoller()
    return await poller.search_item(db, item)

@router.post("/trigger-all")
async def trigger_all(db: AsyncSession = Depends(get_db), user = Depends(get_current_user)):
    poller = EbayPoller()
    return await poller.search_all(db)

@router.get("/budget")
async def get_budget(db: AsyncSession = Depends(get_db), user = Depends(get_current_user)):
    """Get current eBay API budget status for dashboard."""
    poller = EbayPoller()
    return await poller.get_budget_status()

@router.get("/presets")
async def get_presets(user = Depends(get_current_user)):
    """Get polling interval presets for frontend."""
    return {
        "presets": {
            "hot": {"interval": 300, "label": "Hot (5 min)", "daily_calls": 288},
            "standard": {"interval": 600, "label": "Standard (10 min)", "daily_calls": 144},
            "monitor": {"interval": 1200, "label": "Monitor (20 min)", "daily_calls": 72},
            "passive": {"interval": 1800, "label": "Passive (30 min)", "daily_calls": 48},
        }
    }
```

### Task 6: Wire into API Endpoints

Update `backend/app/api/v1/endpoints/search.py` to use the poller:

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.api.deps import get_db, get_current_user
from app.models.tracked_item import TrackedItem
from app.services.ebay.poller import EbayPoller

router = APIRouter(prefix="/search", tags=["search"])

@router.post("/trigger/{item_id}")
async def trigger_search(item_id: int, db: AsyncSession = Depends(get_db), user = Depends(get_current_user)):
    result = await db.execute(select(TrackedItem).where(TrackedItem.id == item_id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    poller = EbayPoller()
    return await poller.search_item(db, item)

@router.post("/trigger-all")
async def trigger_all(db: AsyncSession = Depends(get_db), user = Depends(get_current_user)):
    poller = EbayPoller()
    return await poller.search_all(db)
```

### Task 7: Tests

**`backend/tests/test_ebay.py`**:
```python
import pytest
from app.services.ebay.mock import MockEbayClient
from app.services.ebay.parser import ListingParser

@pytest.mark.asyncio
async def test_mock_search():
    client = MockEbayClient()
    result = await client.search("AMD EPYC 7F72")
    assert "itemSummaries" in result
    assert len(result["itemSummaries"]) > 0
    assert result["itemSummaries"][0]["price"]["value"]

@pytest.mark.asyncio
async def test_parser():
    parser = ListingParser()
    raw = {
        "itemId": "12345",
        "title": "Test CPU",
        "price": {"value": "299.99", "currency": "USD"},
        "seller": {"username": "test_seller", "feedbackScore": 500},
        "itemWebUrl": "https://ebay.com/itm/12345",
        "buyingOptions": ["FIXED_PRICE"],
        "listingDate": "2025-01-01T00:00:00Z"
    }
    parsed = parser.parse_item(raw)
    assert parsed.marketplace_id == "12345"
    assert parsed.price == 299.99
```

---

## Deliverables

- [ ] `app/services/ebay/client.py` — OAuth + Browse API client
- [ ] `app/services/ebay/mock.py` — Mock client for development
- [ ] `app/services/ebay/parser.py` — Response parser
- [ ] `app/services/ebay/dedup.py` — Deduplication engine
- [ ] **`app/services/ebay/rate_budget.py`** — 4-layer API rate budget manager
- [ ] **`app/services/ebay/catalog.py`** — Hardware catalog with 34 SKUs + scam floors
- [ ] `app/services/ebay/poller.py` — Tiered poller with priority scheduling
- [ ] `app/api/v1/endpoints/search.py` — Updated with budget + presets endpoints
- [ ] **`app/api/v1/endpoints/catalog.py`** — Catalog search + categories endpoints
- [ ] `tests/test_ebay.py` — Client + parser tests
- [ ] `tests/test_rate_budget.py` — Rate budget manager tests

## Git
Branch: `phase-03-ebay`
Base: `main` (after Phase 1 merge)
Commit message: `feat(phase-3): eBay Browse API client, parser, dedup, poller`
