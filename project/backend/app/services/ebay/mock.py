import random
from datetime import datetime, timedelta


class MockEbayClient:
    """Mock eBay client for development/testing."""

    MOCK_SELLERS = ["serverdeals", "techliquidators", "datacenterpulls", "homedata", "enterprisehw"]
    MOCK_CONDITIONS = ["Used", "New", "Seller refurbished", "For parts or not working"]

    async def search(self, keywords: str, **kwargs) -> dict:
        count = random.randint(3, 15)
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
                "seller": {
                    "username": random.choice(self.MOCK_SELLERS),
                    "feedbackScore": random.randint(50, 5000),
                    "feedbackPercentage": str(round(random.uniform(95.0, 100.0), 1))
                },
                "condition": random.choice(self.MOCK_CONDITIONS),
                "conditionId": random.choice(["3000", "1000", "2500", "7000"]),
                "itemWebUrl": f"https://www.ebay.com/itm/mock-{i}",
                "image": {"imageUrl": f"https://i.ebayimg.com/mock-{i}.jpg"},
                "buyingOptions": random.choice([["FIXED_PRICE"], ["FIXED_PRICE", "BEST_OFFER"], ["AUCTION"]]),
                "itemEndDate": (datetime.utcnow() + timedelta(days=random.randint(1, 30))).isoformat() + "Z",
                "listingDate": (datetime.utcnow() - timedelta(days=random.randint(0, 7))).isoformat() + "Z",
                "categories": [{"categoryId": kwargs.get("category_id", "164"), "categoryName": "Category"}],
                # Mostly US stock with a sprinkle of China-shipped items so the
                # origin flag is exercised in dev/demo.
                "itemLocation": {"country": random.choice(["US", "US", "US", "CN", "HK"])},
            })

        return {"itemSummaries": items, "total": count, "offset": 0, "limit": 200}

    def _estimate_base_price(self, keywords: str) -> float:
        keyword_lower = keywords.lower()
        price_map = {
            "epyc 7f72": 350.0, "epyc 7443": 450.0, "epyc 7452": 400.0,
            "h12ssl": 700.0, "romed8": 650.0, "mz32": 600.0,
            "rtx pro 6000": 8000.0, "rtx 6000 ada": 5000.0,
            "rtx pro 4000": 1700.0, "l4": 3000.0, "t4": 500.0,
            "m393a8g40mb2": 150.0, "m393a8g40ab2": 160.0, "mta36asf8g72pz": 140.0,
            "p5510": 380.0, "pm9a3": 580.0, "7450": 450.0,
            "connectx-4": 40.0, "connectx-5": 60.0, "connectx-6": 650.0,
            "rm52": 580.0, "rm44": 400.0,
            "exos": 260.0, "ultrastar": 280.0, "mg0": 310.0,
            "corsair hx1500i": 350.0,
        }
        for key, price in price_map.items():
            if key in keyword_lower:
                return price
        return 100.0

    def _generate_title(self, keywords: str) -> str:
        prefixes = ["", "Genuine ", "OEM ", "TESTED ", "Pull ", "Enterprise ", "Datacenter "]
        suffixes = ["", " - Fast Ship", " - Tested Working", " - FREE SHIPPING", " - Server Pull", " Bulk Lot"]
        return f"{random.choice(prefixes)}{keywords}{random.choice(suffixes)}"
