"""Onboarding router endpoints."""

from fastapi import APIRouter, Depends

from src.dependencies import DatabaseDep
from src.schemas.onboarding import BestPracticesResponse, OnboardingResponse
from src.services.onboarding_service import OnboardingService

router = APIRouter(prefix="/onboarding", tags=["onboarding"])


@router.get(
    "",
    response_model=OnboardingResponse,
    summary="Get onboarding materials",
)
async def get_onboarding_materials(
    db: DatabaseDep,
) -> OnboardingResponse:
    """
    Get onboarding materials for new users.

    This endpoint provides structured content to help new users get started,
    including welcome messages, getting started guides, featured collections,
    quick tips, and relevant FAQs.

    Args:
        db: Database session

    Returns:
        OnboardingResponse: Onboarding materials
    """
    return OnboardingService.get_onboarding_materials(db=db)


@router.get(
    "/best-practices",
    response_model=BestPracticesResponse,
    summary="Get best practices for using prompts",
)
async def get_best_practices(
    db: DatabaseDep,
) -> BestPracticesResponse:
    """
    Get best practices and usage tips for prompt engineering.

    This endpoint provides general tips, platform-specific guidance,
    common mistakes to avoid, and helpful resources.

    Args:
        db: Database session

    Returns:
        BestPracticesResponse: Best practices information
    """
    return OnboardingService.get_best_practices(db=db)

