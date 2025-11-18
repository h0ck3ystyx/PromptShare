"""Rating router endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from src.dependencies import CurrentUserDep, DatabaseDep
from src.schemas.common import MessageResponse
from src.schemas.rating import PromptRatingSummary, RatingCreate, RatingResponse, RatingUpdate
from src.services.rating_service import RatingService

router = APIRouter(prefix="/prompts/{prompt_id}/ratings", tags=["ratings"])


@router.post(
    "",
    response_model=RatingResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create or update a rating for a prompt",
)
async def create_or_update_rating(
    prompt_id: UUID,
    rating_data: RatingCreate,
    db: DatabaseDep,
    current_user: CurrentUserDep,
) -> RatingResponse:
    """
    Create or update a rating for a prompt (1-5 stars).

    Args:
        prompt_id: Prompt UUID
        rating_data: Rating data
        db: Database session
        current_user: Current authenticated user

    Returns:
        RatingResponse: Created or updated rating
    """
    rating = RatingService.create_or_update_rating(
        db=db,
        prompt_id=prompt_id,
        rating_data=rating_data,
        user_id=current_user.id,
    )

    # Build response (user relationship already loaded by service)
    rating_dict = {
        "id": rating.id,
        "prompt_id": rating.prompt_id,
        "user_id": rating.user_id,
        "rating": rating.rating,
        "created_at": rating.created_at,
        "author_username": rating.user.username,
    }

    return RatingResponse(**rating_dict)


@router.get(
    "/me",
    response_model=RatingResponse | None,
    summary="Get current user's rating for a prompt",
)
async def get_my_rating(
    prompt_id: UUID,
    db: DatabaseDep,
    current_user: CurrentUserDep,
) -> RatingResponse | None:
    """
    Get the current user's rating for a prompt.

    Args:
        prompt_id: Prompt UUID
        db: Database session
        current_user: Current authenticated user

    Returns:
        RatingResponse: User's rating if exists, None otherwise
    """
    rating = RatingService.get_rating(
        db=db,
        prompt_id=prompt_id,
        user_id=current_user.id,
    )

    if not rating:
        return None

    # Build response (user relationship already loaded by service)
    rating_dict = {
        "id": rating.id,
        "prompt_id": rating.prompt_id,
        "user_id": rating.user_id,
        "rating": rating.rating,
        "created_at": rating.created_at,
        "author_username": rating.user.username,
    }

    return RatingResponse(**rating_dict)


@router.put(
    "/me",
    response_model=RatingResponse,
    summary="Update current user's rating for a prompt",
)
async def update_my_rating(
    prompt_id: UUID,
    rating_data: RatingUpdate,
    db: DatabaseDep,
    current_user: CurrentUserDep,
) -> RatingResponse:
    """
    Update the current user's rating for a prompt.

    Args:
        prompt_id: Prompt UUID
        rating_data: Updated rating data
        db: Database session
        current_user: Current authenticated user

    Returns:
        RatingResponse: Updated rating

    Raises:
        HTTPException: If rating not found
    """
    # Check if rating exists
    existing_rating = RatingService.get_rating(
        db=db,
        prompt_id=prompt_id,
        user_id=current_user.id,
    )

    if not existing_rating:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rating not found. Use POST to create a new rating.",
        )

    # Update using create_or_update (which handles updates)
    rating = RatingService.create_or_update_rating(
        db=db,
        prompt_id=prompt_id,
        rating_data=RatingCreate(rating=rating_data.rating),
        user_id=current_user.id,
    )

    # Build response (user relationship already loaded by service)
    rating_dict = {
        "id": rating.id,
        "prompt_id": rating.prompt_id,
        "user_id": rating.user_id,
        "rating": rating.rating,
        "created_at": rating.created_at,
        "author_username": rating.user.username,
    }

    return RatingResponse(**rating_dict)


@router.delete(
    "/me",
    response_model=MessageResponse,
    summary="Delete current user's rating for a prompt",
)
async def delete_my_rating(
    prompt_id: UUID,
    db: DatabaseDep,
    current_user: CurrentUserDep,
) -> MessageResponse:
    """
    Delete the current user's rating for a prompt.

    Args:
        prompt_id: Prompt UUID
        db: Database session
        current_user: Current authenticated user

    Returns:
        MessageResponse: Success message
    """
    RatingService.delete_rating(
        db=db,
        prompt_id=prompt_id,
        user_id=current_user.id,
    )

    return MessageResponse(message="Rating deleted successfully")


@router.get(
    "/summary",
    response_model=PromptRatingSummary,
    summary="Get rating summary for a prompt",
)
async def get_rating_summary(
    prompt_id: UUID,
    db: DatabaseDep,
) -> PromptRatingSummary:
    """
    Get rating summary for a prompt (average, total, distribution).

    Args:
        prompt_id: Prompt UUID
        db: Database session

    Returns:
        PromptRatingSummary: Rating summary
    """
    summary = RatingService.get_rating_summary(db=db, prompt_id=prompt_id)

    return PromptRatingSummary(**summary)

