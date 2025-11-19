"""Analytics router endpoints (admin only)."""

from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status

from src.dependencies import AdminDep, DatabaseDep
from src.schemas.analytics import OverviewAnalyticsResponse, PromptAnalyticsResponse
from src.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get(
    "/prompts/{prompt_id}",
    response_model=PromptAnalyticsResponse,
    summary="Get analytics for a specific prompt (admin only)",
)
async def get_prompt_analytics(
    prompt_id: UUID,
    db: DatabaseDep,
    admin: AdminDep,
    days: int = Query(30, ge=1, le=365, description="Number of days to look back"),
) -> PromptAnalyticsResponse:
    """
    Get analytics for a specific prompt.

    Args:
        prompt_id: Prompt UUID to get analytics for
        db: Database session
        admin: Admin user (required)
        days: Number of days to look back (default: 30, max: 365)

    Returns:
        PromptAnalyticsResponse: Analytics data for the prompt

    Raises:
        HTTPException: If prompt not found or user is not admin
    """
    try:
        analytics = AnalyticsService.get_prompt_analytics(
            db=db,
            prompt_id=prompt_id,
            days=days,
        )
        return PromptAnalyticsResponse(**analytics)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.get(
    "/overview",
    response_model=OverviewAnalyticsResponse,
    summary="Get overall platform analytics (admin only)",
)
async def get_overview_analytics(
    db: DatabaseDep,
    admin: AdminDep,
    days: int = Query(30, ge=1, le=365, description="Number of days to look back"),
) -> OverviewAnalyticsResponse:
    """
    Get overall analytics for the platform.

    Args:
        db: Database session
        admin: Admin user (required)
        days: Number of days to look back (default: 30, max: 365)

    Returns:
        OverviewAnalyticsResponse: Overall analytics data

    Raises:
        HTTPException: If user is not admin
    """
    analytics = AnalyticsService.get_overview_analytics(
        db=db,
        days=days,
    )
    return OverviewAnalyticsResponse(**analytics)

