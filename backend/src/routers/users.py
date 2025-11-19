"""User router endpoints."""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from src.constants import UserRole
from src.dependencies import (
    AdminDep,
    CurrentUserDep,
    DatabaseDep,
)
from src.schemas.common import MessageResponse, PaginatedResponse
from src.schemas.user import (
    UserResponse,
    UserRoleUpdate,
    UserStats,
    UserStatusUpdate,
    UserUpdate,
)
from src.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["users"])


@router.get(
    "",
    response_model=PaginatedResponse[UserResponse],
    summary="List users (admin only)",
)
async def list_users(
    db: DatabaseDep,
    admin_user: AdminDep,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    role: Optional[UserRole] = Query(None, description="Filter by role"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    search: Optional[str] = Query(None, description="Search in username, email, or full name"),
) -> PaginatedResponse[UserResponse]:
    """
    List all users with pagination and filters (admin only).

    Args:
        db: Database session
        admin_user: Current admin user
        page: Page number (1-indexed)
        page_size: Number of items per page
        role: Filter by user role
        is_active: Filter by active status
        search: Search query

    Returns:
        PaginatedResponse: Paginated list of users
    """
    skip = (page - 1) * page_size

    users, total = UserService.get_users(
        db=db,
        skip=skip,
        limit=page_size,
        role_filter=role,
        is_active=is_active,
        search_query=search,
    )

    user_responses = [UserResponse.model_validate(user) for user in users]
    total_pages = (total + page_size - 1) // page_size

    return PaginatedResponse(
        items=user_responses,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user profile",
)
async def get_my_profile(
    db: DatabaseDep,
    current_user: CurrentUserDep,
) -> UserResponse:
    """
    Get current authenticated user's profile.

    Args:
        db: Database session
        current_user: Current authenticated user

    Returns:
        UserResponse: Current user profile
    """
    return UserResponse.model_validate(current_user)


@router.put(
    "/me",
    response_model=UserResponse,
    summary="Update current user profile",
)
async def update_my_profile(
    user_data: UserUpdate,
    db: DatabaseDep,
    current_user: CurrentUserDep,
) -> UserResponse:
    """
    Update current authenticated user's profile.

    Args:
        user_data: User update data
        db: Database session
        current_user: Current authenticated user

    Returns:
        UserResponse: Updated user profile
    """
    updated_user = UserService.update_user_profile(
        db=db,
        user_id=current_user.id,
        user_data=user_data,
        current_user=current_user,
    )

    return UserResponse.model_validate(updated_user)


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    summary="Get user profile",
)
async def get_user_profile(
    user_id: UUID,
    db: DatabaseDep,
    current_user: CurrentUserDep,
) -> UserResponse:
    """
    Get user profile by ID.

    Args:
        user_id: User UUID
        db: Database session
        current_user: Current authenticated user

    Returns:
        UserResponse: User profile
    """
    user = UserService.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return UserResponse.model_validate(user)


@router.put(
    "/{user_id}",
    response_model=UserResponse,
    summary="Update user profile (admin or own profile)",
)
async def update_user(
    user_id: UUID,
    user_data: UserUpdate,
    db: DatabaseDep,
    current_user: CurrentUserDep,
) -> UserResponse:
    """
    Update user profile. Users can update their own profile, admins can update any profile.

    Args:
        user_id: User UUID to update
        user_data: User update data
        db: Database session
        current_user: Current authenticated user

    Returns:
        UserResponse: Updated user profile
    """
    updated_user = UserService.update_user_profile(
        db=db,
        user_id=user_id,
        user_data=user_data,
        current_user=current_user,
    )

    return UserResponse.model_validate(updated_user)


@router.put(
    "/{user_id}/role",
    response_model=UserResponse,
    summary="Update user role (admin only)",
)
async def update_user_role(
    user_id: UUID,
    role_data: UserRoleUpdate,
    db: DatabaseDep,
    admin_user: AdminDep,
) -> UserResponse:
    """
    Update user role (admin only).

    Args:
        user_id: User UUID to update
        role_data: New role
        db: Database session
        admin_user: Current admin user

    Returns:
        UserResponse: Updated user profile
    """
    updated_user = UserService.update_user_role(
        db=db,
        user_id=user_id,
        new_role=role_data.role,
        admin_user=admin_user,
    )

    return UserResponse.model_validate(updated_user)


@router.put(
    "/{user_id}/status",
    response_model=UserResponse,
    summary="Activate or deactivate user (admin only)",
)
async def update_user_status(
    user_id: UUID,
    status_data: UserStatusUpdate,
    db: DatabaseDep,
    admin_user: AdminDep,
) -> UserResponse:
    """
    Activate or deactivate user account (admin only).

    Args:
        user_id: User UUID to update
        status_data: New active status
        db: Database session
        admin_user: Current admin user

    Returns:
        UserResponse: Updated user profile
    """
    updated_user = UserService.update_user_status(
        db=db,
        user_id=user_id,
        is_active=status_data.is_active,
        admin_user=admin_user,
    )

    return UserResponse.model_validate(updated_user)


@router.get(
    "/{user_id}/stats",
    response_model=UserStats,
    summary="Get user statistics",
)
async def get_user_stats(
    user_id: UUID,
    db: DatabaseDep,
    current_user: CurrentUserDep,
) -> UserStats:
    """
    Get user statistics (prompts, comments, ratings, upvotes).
    Users can view their own stats, admins and moderators can view any user's stats.

    Args:
        user_id: User UUID
        db: Database session
        current_user: Current authenticated user

    Returns:
        UserStats: User statistics

    Raises:
        HTTPException: If user not authorized to view these statistics
    """
    # Authorization check: only own stats or admin/moderator
    if user_id != current_user.id:
        if current_user.role not in (UserRole.ADMIN, UserRole.MODERATOR):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view this user's statistics",
            )

    stats = UserService.get_user_stats(db, user_id)
    return UserStats(**stats)

