from fastapi import APIRouter, Depends, HTTPException, Query
from app.api.deps import get_current_user
from app.models.user import User
from app.services.ebay.catalog import HardwareCatalog

router = APIRouter(prefix="/catalog", tags=["catalog"])


@router.get("")
async def search_catalog(
    q: str = Query(..., min_length=1),
    user: User = Depends(get_current_user)
):
    results = HardwareCatalog.search(q)
    return [{
        "name": r.name,
        "keywords": r.keywords,
        "sku": r.sku,
        "mpn": r.mpn,
        "category_id": r.category_id,
        "target_price": r.target_price,
        "alert_threshold": r.alert_threshold,
        "search_interval": r.search_interval,
        "benchmark_median": r.benchmark_median,
        "scam_floor": r.scam_floor,
        "notes": r.notes,
    } for r in results[:10]]


@router.get("/categories")
async def get_categories(user: User = Depends(get_current_user)):
    return HardwareCatalog.get_categories()
