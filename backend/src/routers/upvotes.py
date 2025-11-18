"""Upvote router endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, status

from src.dependencies import CurrentUserDep, DatabaseDep, OptionalUserDep
from src.schemas.common import MessageResponse
from src.schemas.upvote import PromptUpvoteSummary, UpvoteResponse
from src.services.upvote_service import UpvoteService

router = APIRouter(prefix="/prompts/{prompt_id}/upvotes", tags=["upvotes"])


@router.post(
    "",
    response_model=UpvoteResponse | MessageResponse,
    summary="Toggle upvote for a prompt",
)
async def toggle_upvote(
    prompt_id: UUID,
    db: DatabaseDep,
    current_user: CurrentUserDep,
) -> UpvoteResponse | MessageResponse:
    """
    Toggle upvote for a prompt (add if not exists, remove if exists).

    Args:
        prompt_id: Prompt UUID
        db: Database session
        current_user: Current authenticated user

    Returns:
        UpvoteResponse: If upvote was added
        MessageResponse: If upvote was removed
    """
    upvote, is_upvoted = UpvoteService.toggle_upvote(
        db=db,
        prompt_id=prompt_id,
        user_id=current_user.id,
    )

    if is_upvoted:
        return UpvoteResponse.model_validate(upvote)
    else:
        return MessageResponse(message="Upvote removed successfully")


@router.get(
    "/me",
    summary="Check if current user has upvoted a prompt",
)
async def check_my_upvote(
    prompt_id: UUID,
    db: DatabaseDep,
    current_user: CurrentUserDep,
) -> dict:
    """
    Check if the current user has upvoted a prompt.

    Args:
        prompt_id: Prompt UUID
        db: Database session
        current_user: Current authenticated user

    Returns:
        dict: Information about user's upvote status
    """
    has_upvoted = UpvoteService.has_user_upvoted(
        db=db,
        prompt_id=prompt_id,
        user_id=current_user.id,
    )

    return {"has_upvoted": has_upvoted}


@router.get(
    "/summary",
    response_model=PromptUpvoteSummary,
    summary="Get upvote summary for a prompt",
)
async def get_upvote_summary(
    prompt_id: UUID,
    db: DatabaseDep,
    current_user: OptionalUserDep = None,
) -> PromptUpvoteSummary:
    """
    Get upvote summary for a prompt.

    Args:
        prompt_id: Prompt UUID
        db: Database session
        current_user: Current authenticated user (optional)

    Returns:
        PromptUpvoteSummary: Upvote summary
    """
    total_upvotes = UpvoteService.get_upvote_count(db=db, prompt_id=prompt_id)

    user_has_upvoted = False
    if current_user:
        user_has_upvoted = UpvoteService.has_user_upvoted(
            db=db,
            prompt_id=prompt_id,
            user_id=current_user.id,
        )

    return PromptUpvoteSummary(
        prompt_id=prompt_id,
        total_upvotes=total_upvotes,
        user_has_upvoted=user_has_upvoted,
    )

