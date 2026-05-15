from fastapi import APIRouter
from app.api.v1.endpoints import auth, items, search, catalog, deals, settings, alerts

router = APIRouter(prefix="/api/v1")

router.include_router(auth.router, prefix="/auth")
router.include_router(items.router, prefix="/items")
router.include_router(search.router, prefix="/search")
router.include_router(catalog.router, prefix="/catalog")
router.include_router(deals.router, prefix="/deals")
router.include_router(settings.router, prefix="/settings")
router.include_router(alerts.router, prefix="/alerts")


@router.get("/health")
async def health_check():
    return {"status": "healthy", "version": "0.2.0"}
