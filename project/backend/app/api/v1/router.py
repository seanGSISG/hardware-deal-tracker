from fastapi import APIRouter

from app.api.v1.endpoints import (
    ai,
    alerts,
    auth,
    catalog,
    community,
    deals,
    history,
    items,
    search,
    semantic,
    settings,
)

router = APIRouter(prefix="/api/v1")

router.include_router(auth.router)
router.include_router(items.router)
router.include_router(search.router)
router.include_router(catalog.router)
router.include_router(deals.router)
router.include_router(settings.router)
router.include_router(alerts.router)
router.include_router(history.router)
router.include_router(ai.router)
router.include_router(semantic.router)
router.include_router(community.router)


@router.get("/health")
async def health_check():
    return {"status": "healthy", "version": "0.2.0"}
