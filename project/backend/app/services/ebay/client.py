import time
import httpx
from typing import Optional
from app.core.config import settings


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
            "scope": "https://api.ebay.com/oauth/api_scope"
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
        if self._daily_calls >= 4800:
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
            joined = "|".join(buying_options)
            filters.append(f"buyingOptions:{{{joined}}}")
        if condition_ids:
            joined = "|".join(condition_ids)
            filters.append(f"conditionIds:{{{joined}}}")
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
