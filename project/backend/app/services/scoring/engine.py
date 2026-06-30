
from app.models.listing import Listing


class DealScoringEngine:
    """Rules-based deal scoring with weighted components and scam detection.

    The benchmark price is derived solely from the historical stats passed in
    or, as a fallback, the catalog item's ``benchmark_median`` — the catalog is
    the single source of truth. There is intentionally no hard-coded benchmark
    table here (it drifts from the catalog and breaks fresh/empty-DB setups).
    """

    def calculate_z_score(self, price: float, mean_price: float, std_dev: float) -> float:
        if std_dev == 0:
            return 0.0
        return (price - mean_price) / std_dev

    def score_price_zscore(self, z_score: float) -> int:
        if z_score <= -2.0:
            return 100
        elif z_score <= -1.5:
            return 85
        elif z_score <= -1.0:
            return 70
        elif z_score <= -0.5:
            return 50
        elif z_score <= 0:
            return 30
        elif z_score <= 0.5:
            return 15
        else:
            return max(0, 30 - int(z_score * 20))

    def score_historical_discount(self, price: float, median_price: float) -> int:
        if median_price <= 0:
            return 50
        discount_pct = (median_price - price) / median_price
        if discount_pct >= 0.50:
            return 100
        elif discount_pct >= 0.30:
            return 70 + int((discount_pct - 0.30) / 0.20 * 30)
        elif discount_pct >= 0.15:
            return 40 + int((discount_pct - 0.15) / 0.15 * 30)
        elif discount_pct >= 0:
            return 20 + int(discount_pct / 0.15 * 20)
        else:
            return max(0, 20 + int(discount_pct * 100))

    def score_seller_quality(self, feedback_score: int, positive_pct: float) -> int:
        if feedback_score >= 1000 and positive_pct >= 99.0:
            return 100
        elif feedback_score >= 500 and positive_pct >= 98.0:
            return 90
        elif feedback_score >= 100 and positive_pct >= 97.0:
            return 75
        elif feedback_score >= 50 and positive_pct >= 95.0:
            return 60
        elif feedback_score >= 10:
            return 40
        elif feedback_score > 0:
            return 25
        else:
            return 15

    def score_listing_quality(self, title: str, condition: str | None) -> int:
        score = 80
        title_lower = title.lower()
        penalties = {
            "for dell only": 30, "for hp only": 30, "for ibm only": 30,
            "untested": 20, "as-is": 25, "for parts": 40, "not working": 40,
        }
        for phrase, penalty in penalties.items():
            if phrase in title_lower:
                score -= penalty
        if condition:
            if "new" in condition.lower():
                score += 20
            elif "for parts" in condition.lower():
                score -= 30
        return max(0, min(100, score))

    def calculate_overall_score(
        self,
        listing: Listing,
        historical_stats: dict,
        catalog_item=None
    ) -> dict:
        total_price = float(listing.price) + float(listing.shipping)
        median_price = historical_stats.get("median_price")
        mean_price = historical_stats.get("avg_price")
        std_dev = historical_stats.get("std_dev", 0)

        # Coerce catalog benchmark/scam_floor to float: persisted TrackedItem rows
        # expose these as decimal.Decimal (SQLAlchemy Numeric), which can't be
        # mixed with float arithmetic. Fresh/empty-DB items flow through here.
        benchmark = None
        scam_floor = 0.0
        if catalog_item is not None:
            if catalog_item.benchmark_median is not None:
                benchmark = float(catalog_item.benchmark_median)
            if catalog_item.scam_floor is not None:
                scam_floor = float(catalog_item.scam_floor)

        if median_price is None and benchmark is not None:
            median_price = benchmark
            mean_price = benchmark
            std_dev = benchmark * 0.15
        # Per-unit normalization (lots): the catalog benchmark/scam_floor are
        # per-module, so a multi-stick lot must be judged on its $/stick — else
        # an 8x lot's total dwarfs the single-stick median and every price
        # component scores it as "way over market". quantity==1 leaves unit_price
        # == total_price, so single listings are unaffected.
        quantity = getattr(listing, "quantity", 1) or 1
        unit_price = total_price / quantity

        # No history and no catalog benchmark: fall back to the listing's own
        # per-unit price (a lone listing scores neutral).
        if median_price is None:
            median_price = unit_price
            mean_price = unit_price
            std_dev = 0

        # Check scam floor (per-unit)
        scam_warning = None
        if scam_floor > 0 and unit_price < scam_floor:
            qual = f" (${unit_price:.2f}/unit x{quantity})" if quantity > 1 else ""
            scam_warning = f"Price ${unit_price:.2f} below scam floor ${scam_floor:.2f}{qual}"

        z_score = self.calculate_z_score(unit_price, mean_price or median_price, std_dev or 1)
        zscore_score = self.score_price_zscore(z_score)
        discount_score = self.score_historical_discount(unit_price, median_price)
        seller_score = self.score_seller_quality(listing.seller_feedback, float(listing.seller_positive_pct))
        quality_score = self.score_listing_quality(listing.title, listing.condition)
        timing_score = 50

        # Extra bonus for buying in bulk below median (on top of the per-unit
        # discount already captured above).
        bulk_score = 50
        if quantity > 1:
            discount = (median_price - unit_price) / median_price if median_price > 0 else 0
            bulk_score = min(100, max(0, int(discount * 150)))

        overall = round(
            zscore_score * 0.30 +
            discount_score * 0.25 +
            seller_score * 0.15 +
            quality_score * 0.15 +
            timing_score * 0.10 +
            bulk_score * 0.05
        )

        deal_score = round(
            zscore_score * 0.40 +
            discount_score * 0.35 +
            bulk_score * 0.15 +
            seller_score * 0.10
        )

        data_points = historical_stats.get("data_points", 0)
        if data_points >= 50:
            confidence = 0.95
        elif data_points >= 20:
            confidence = 0.80
        elif data_points >= 5:
            confidence = 0.60
        elif catalog_item:
            confidence = 0.45
        else:
            confidence = 0.30

        if overall >= 85:
            classification = "hot_deal"
        elif overall >= 70:
            classification = "great_deal"
        elif overall >= 50:
            classification = "good_deal"
        elif overall >= 30:
            classification = "fair_deal"
        else:
            classification = "poor_deal"

        # Override for scams
        if scam_warning:
            overall = min(overall, 30)
            classification = "suspicious"

        vs_median = (median_price - total_price) / median_price if median_price > 0 else 0
        lowest = historical_stats.get("min_price")
        vs_lowest = (lowest - total_price) / lowest if lowest and lowest > 0 else 0

        return {
            "overall_score": min(100, max(0, overall)),
            "deal_score": min(100, max(0, deal_score)),
            "confidence": round(confidence, 2),
            "classification": classification,
            "price_zscore": round(z_score, 4),
            "vs_median_pct": round(vs_median, 4),
            "vs_lowest_pct": round(vs_lowest, 4),
            "est_fair_value": round(median_price, 2),
            "scam_warning": scam_warning,
        }
