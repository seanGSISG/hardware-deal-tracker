from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.ai_analysis import AIAnalysis
from app.models.user import User

router = APIRouter(prefix="/ai", tags=["ai"])


@router.get("/{listing_id}")
async def get_listing_analysis(
    listing_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Latest AI analysis for a listing, or {analysis: null} if none exists."""
    row = (
        await db.execute(
            select(AIAnalysis)
            .where(AIAnalysis.listing_id == listing_id)
            .order_by(AIAnalysis.created_at.desc(), AIAnalysis.id.desc())
            .limit(1)
        )
    ).scalar_one_or_none()

    if row is None:
        return {"analysis": None}

    return {
        "analysis": {
            "deal_grade": row.deal_grade,
            "reasoning": row.reasoning,
            "scam_signal": row.scam_signal,
            "scam_reasons": row.scam_reasons,
            "extracted_specs": row.extracted_specs,
            "provider": row.provider,
            "model": row.model,
            "created_at": row.created_at.isoformat() if row.created_at else None,
        }
    }
