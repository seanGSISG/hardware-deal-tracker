from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, and_
from typing import Optional
from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.models.listing import Listing
from app.models.listing_score import ListingScore
from app.schemas.deal import DealListResponse

router = APIRouter(prefix="/deals", tags=["deals"])


@router.get("")
async def list_deals(
    min_score: int = Query(50, ge=0, le=100),
    max_score: int = Query(100, ge=0, le=100),
    item_id: Optional[int] = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    query = (
        select(Listing, ListingScore)
        .join(ListingScore, Listing.id == ListingScore.listing_id)
        .where(
            and_(
                ListingScore.overall_score >= min_score,
                ListingScore.overall_score <= max_score
            )
        )
        .order_by(desc(ListingScore.overall_score))
    )
    if item_id:
        query = query.where(Listing.tracked_item_id == item_id)

    count_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = count_result.scalar()

    query = query.offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(query)
    rows = result.all()

    deals = []
    for listing, score in rows:
        deal_dict = {k: v for k, v in listing.__dict__.items() if not k.startswith("_")}
        deal_dict["score"] = {
            "overall_score": score.overall_score,
            "deal_score": score.deal_score,
            "confidence": float(score.confidence),
            "classification": score.classification,
            "price_zscore": float(score.price_zscore) if score.price_zscore else None,
            "vs_median_pct": float(score.vs_median_pct) if score.vs_median_pct else None,
            "est_fair_value": float(score.est_fair_value) if score.est_fair_value else None,
            "scam_warning": score.scam_flag,
        }
        deals.append(deal_dict)

    return {"deals": deals, "total": total, "page": page, "per_page": per_page}


@router.post("/score/{listing_id}")
async def score_listing(
    listing_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    from app.services.scoring.engine import DealScoringEngine
    from app.services.ebay.catalog import HardwareCatalog

    result = await db.execute(select(Listing).where(Listing.id == listing_id))
    listing = result.scalar_one_or_none()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")

    # Get tracked item for catalog lookup
    catalog_item = None
    if listing.tracked_item_id:
        item_result = await db.execute(select(TrackedItem).where(TrackedItem.id == listing.tracked_item_id))
        tracked_item = item_result.scalar_one_or_none()
        if tracked_item:
            catalog_item = HardwareCatalog.get_by_name(tracked_item.name)

    engine = DealScoringEngine()
    score_data = engine.calculate_overall_score(listing, {}, catalog_item)

    score = ListingScore(
        listing_id=listing_id,
        tracked_item_id=listing.tracked_item_id,
        overall_score=score_data["overall_score"],
        deal_score=score_data["deal_score"],
        confidence=score_data["confidence"],
        classification=score_data["classification"],
        price_zscore=score_data.get("price_zscore"),
        vs_median_pct=score_data.get("vs_median_pct"),
        vs_lowest_pct=score_data.get("vs_lowest_pct"),
        est_fair_value=score_data.get("est_fair_value"),
        scam_flag=score_data.get("scam_warning"),
    )
    db.add(score)
    await db.flush()

    return score_data


@router.get("/{deal_id}")
async def get_deal(
    deal_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(Listing, ListingScore)
        .join(ListingScore, Listing.id == ListingScore.listing_id)
        .where(Listing.id == deal_id)
    )
    row = result.first()
    if not row:
        raise HTTPException(status_code=404, detail="Deal not found")
    listing, score = row
    return {
        **{k: v for k, v in listing.__dict__.items() if not k.startswith("_")},
        "score": score,
    }
