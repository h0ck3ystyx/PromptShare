"""Follow router endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from src.dependencies import CurrentUserDep, DatabaseDep
from src.models.user_follow import UserFollow
from src.schemas.common import MessageResponse, PaginatedResponse
from src.schemas.follow import FollowResponse
from src.services.follow_service import FollowService

router = APIRouter(prefix="/follows", tags=["follows"])


@router.post(
    "/categories/{category_id}",
    response_model=FollowResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Follow a category",
)
async def follow_category(
    category_id: UUID,
    db: DatabaseDep,
    current_user: CurrentUserDep,
) -> FollowResponse:
    """
    Follow a category to receive notifications about new prompts.

    Args:
        category_id: ID of the category to follow
        db: Database session
        current_user: Current authenticated user

    Returns:
        FollowResponse: The created follow relationship

    Raises:
        HTTPException: If category not found or already following
    """
    follow = FollowService.follow_category(
        db=db,
        user_id=current_user.id,
        category_id=category_id,
    )

    # Load category relationship
    db.refresh(follow)
    return FollowResponse(
        id=follow.id,
        user_id=follow.user_id,
        category_id=follow.category_id,
        created_at=follow.created_at,
        category=follow.category,
    )


@router.delete(
    "/categories/{category_id}",
    response_model=MessageResponse,
    summary="Unfollow a category",
)
async def unfollow_category(
    category_id: UUID,
    db: DatabaseDep,
    current_user: CurrentUserDep,
) -> MessageResponse:
    """
    Unfollow a category.

    Args:
        category_id: ID of the category to unfollow
        db: Database session
        current_user: Current authenticated user

    Returns:
        MessageResponse: Success message

    Raises:
        HTTPException: If not following this category
    """
    FollowService.unfollow_category(
        db=db,
        user_id=current_user.id,
        category_id=category_id,
    )

    return MessageResponse(message="Successfully unfollowed category")


@router.get(
    "/categories",
    response_model=PaginatedResponse[FollowResponse],
    summary="Get categories followed by current user",
)
async def get_my_follows(
    db: DatabaseDep,
    current_user: CurrentUserDep,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
) -> PaginatedResponse[FollowResponse]:
    """
    Get categories followed by the current user.

    Args:
        db: Database session
        current_user: Current authenticated user
        page: Page number (1-indexed)
        page_size: Number of items per page

    Returns:
        PaginatedResponse: Paginated list of followed categories
    """
    skip = (page - 1) * page_size
    
    # Get all follow relationships for this user with categories loaded
    from sqlalchemy.orm import joinedload
    follow_rels = (
        db.query(UserFollow)
        .options(joinedload(UserFollow.category))
        .filter(UserFollow.user_id == current_user.id)
        .order_by(UserFollow.created_at.desc())
        .offset(skip)
        .limit(page_size)
        .all()
    )

    # Get total count
    total = db.query(UserFollow).filter(UserFollow.user_id == current_user.id).count()

    follow_responses = []
    for follow_rel in follow_rels:
        if follow_rel.category:
            follow_responses.append(
                FollowResponse(
                    id=follow_rel.id,
                    user_id=follow_rel.user_id,
                    category_id=follow_rel.category_id,
                    created_at=follow_rel.created_at,
                    category=follow_rel.category,
                )
            )

    total_pages = (total + page_size - 1) // page_size

    return PaginatedResponse(
        items=follow_responses,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get(
    "/categories/{category_id}/check",
    response_model=dict,
    summary="Check if current user is following a category",
)
async def check_follow_status(
    category_id: UUID,
    db: DatabaseDep,
    current_user: CurrentUserDep,
) -> dict:
    """
    Check if the current user is following a category.

    Args:
        category_id: ID of the category to check
        db: Database session
        current_user: Current authenticated user

    Returns:
        dict: Follow status
    """
    is_following = FollowService.is_following_category(
        db=db,
        user_id=current_user.id,
        category_id=category_id,
    )

    return {"is_following": is_following, "category_id": str(category_id)}

