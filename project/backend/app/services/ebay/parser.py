import contextlib
from datetime import datetime


class ListingParser:
    """Parse eBay Browse API responses into ListingCreate schemas."""

    def parse_item(self, item: dict, tracked_item_id: int | None = None) -> dict:
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
            with contextlib.suppress(ValueError, TypeError):
                listing_date = datetime.fromisoformat(item["listingDate"].replace("Z", "+00:00")).replace(tzinfo=None)

        categories = item.get("categories", [])
        category_id = categories[0].get("categoryId") if categories else None

        return {
            "source": "ebay",
            "marketplace_id": str(item.get("itemId", "")),
            "tracked_item_id": tracked_item_id,
            "title": item.get("title", ""),
            "price": price,
            "shipping": shipping,
            "seller": seller_data.get("username", "unknown"),
            "seller_feedback": feedback_score,
            "seller_positive_pct": feedback_pct,
            "condition": item.get("condition"),
            "condition_id": item.get("conditionId"),
            "category_id": category_id,
            "url": item.get("itemWebUrl", ""),
            "image_url": item.get("image", {}).get("imageUrl") if item.get("image") else None,
            "is_auction": "AUCTION" in buying_options and "FIXED_PRICE" not in buying_options,
            "buying_options": buying_options,
            "listing_date": listing_date,
            "raw_data": item,
        }

    def parse_search_response(self, response: dict, tracked_item_id: int | None = None) -> list:
        items = response.get("itemSummaries", [])
        return [self.parse_item(item, tracked_item_id) for item in items]
