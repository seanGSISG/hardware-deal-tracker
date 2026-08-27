import contextlib
import re
from datetime import datetime

from app.core.config import settings

# Lot-size detection from listing titles. eBay Browse has no structured lot/kit
# field, so quantity is read from the title and fed to the scoring engine's
# per-unit logic (an 8x lot is then judged on its $/stick, not the lot total).
#
# Conservative on purpose:
#   - only counts a number when it's bound to a lot/multiplier token, so memory
#     rank notation ("2Rx4", "4Rx4") and spec digits ("DDR4", "PC4-3200", "32GB")
#     are NOT matched (the `x` patterns require a word boundary before/after).
#   - if a title advertises several sizes ("2x 4x 8x ... pick your qty"), the
#     size is ambiguous and we fall back to 1 rather than guess the priced qty.
_LOT_PATTERNS = (
    r"\blot\s+of\s+(\d{1,2})\b",   # "lot of 8"
    r"\bqty\.?\s*(\d{1,2})\b",     # "qty 8", "qty. 8"
    r"\b(\d{1,2})\s*x\b",          # "8x", "8 x"
    # NOTE: the mirror pattern `\bx\s*(\d{1,2})\b` ("x8", "x16") was REMOVED
    # 2026-08-26. Measured against the live 4,665-listing table it was the sole
    # source of a >1 quantity on 790 rows and was wrong on every one of them:
    # PCIe lane widths ("PCIe 3.0 x4") and model names ("Seagate Exos X16").
    # Those rows had their price divided by 4-16, fell under scam_floor, and
    # scored "suspicious" -- i.e. the alert was muted. Genuine lots are
    # number-first ("8x 32GB", "(3x) ...") or spelled out ("lot of 8", "qty 4"),
    # all of which the remaining patterns cover.
    r"\((\d{1,2})\s*x",            # "(8x 32GB)"
)


# PCIe lane-width notation is NOT a lot size. Without this, "PCIe 5.0 x16" on a
# GPU/NIC/HBA title matched the `x8`/`x16` lot patterns, the scorer divided the
# price by the lane count, and the resulting $/unit fell under scam_floor - which
# caps the overall score at 30 and silently MUTES the alert for that listing.
# Strip the lane token first, and only where it is bound to a PCIe mention, so a
# genuine "lot of 4" in a PCIe card's title still counts.
_PCIE_LANES = re.compile(
    r"pci(?:\s*[-_]\s*|\s+)?e(?:xpress)?\s*(?:gen\s*)?[0-9.]*\s*x\s*\d{1,2}",
    re.IGNORECASE,
)


def detect_lot_size(title: str) -> int:
    """Best-effort lot size (number of modules) from a listing title; 1 if single
    or ambiguous. Only sizes 2..16 are treated as lots."""
    if not title:
        return 1
    t = _PCIE_LANES.sub(" ", title.lower())
    found: set[int] = set()
    for pat in _LOT_PATTERNS:
        for m in re.finditer(pat, t):
            n = int(m.group(1))
            if 2 <= n <= 16:
                found.add(n)
    return found.pop() if len(found) == 1 else 1


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

        # Item origin (eBay Browse summaries carry itemLocation.country as an
        # ISO-3166 alpha-2 code). Used to flag China-shipped listings in the UI.
        item_location = item.get("itemLocation") or {}
        item_country = item_location.get("country")
        china_codes = {c.upper() for c in settings.CHINA_ORIGIN_CODES}
        is_china = bool(item_country) and item_country.upper() in china_codes

        return {
            "source": "ebay",
            "marketplace_id": str(item.get("itemId", "")),
            "tracked_item_id": tracked_item_id,
            "title": item.get("title", ""),
            "quantity": detect_lot_size(item.get("title", "")),
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
            "item_country": item_country,
            "is_china": is_china,
            "raw_data": item,
        }

    def parse_search_response(self, response: dict, tracked_item_id: int | None = None) -> list:
        items = response.get("itemSummaries", [])
        return [self.parse_item(item, tracked_item_id) for item in items]
