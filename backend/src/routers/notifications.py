"""Notification router endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from src.dependencies import CurrentUserDep, DatabaseDep
from src.schemas.common import MessageResponse, PaginatedResponse
from src.schemas.notification import NotificationResponse
from src.services.notification_service import NotificationService

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get(
    "",
    response_model=dict,
    summary="Get notifications for current user",
)
async def get_notifications(
    db: DatabaseDep,
    current_user: CurrentUserDep,
    unread_only: bool = Query(False, description="Only return unread notifications"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
) -> PaginatedResponse[NotificationResponse]:
    """
    Get notifications for the current user.

    Args:
        db: Database session
        current_user: Current authenticated user
        unread_only: If True, only return unread notifications
        page: Page number (1-indexed)
        page_size: Number of items per page

    Returns:
        PaginatedResponse: Paginated list of notifications
    """
    skip = (page - 1) * page_size
    notifications, total = NotificationService.get_user_notifications(
        db=db,
        user_id=current_user.id,
        unread_only=unread_only,
        skip=skip,
        limit=page_size,
    )

    # Get unread count
    unread_count = NotificationService.get_unread_count(db=db, user_id=current_user.id)

    # Convert to response format
    notification_responses = [
        NotificationResponse.model_validate(notification) for notification in notifications
    ]

    total_pages = (total + page_size - 1) // page_size

    # Create response with unread_count included
    response = PaginatedResponse(
        items=notification_responses,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )
    
    # Add unread_count to response (extend the response dict)
    response_dict = response.model_dump()
    response_dict["unread_count"] = unread_count
    
    return response_dict


@router.get(
    "/unread-count",
    response_model=dict,
    summary="Get unread notification count",
)
async def get_unread_count(
    db: DatabaseDep,
    current_user: CurrentUserDep,
) -> dict:
    """
    Get count of unread notifications for the current user.

    Args:
        db: Database session
        current_user: Current authenticated user

    Returns:
        dict: Unread count
    """
    count = NotificationService.get_unread_count(db=db, user_id=current_user.id)
    return {"unread_count": count}


@router.patch(
    "/{notification_id}/read",
    response_model=NotificationResponse,
    summary="Mark a notification as read",
)
async def mark_notification_as_read(
    notification_id: UUID,
    db: DatabaseDep,
    current_user: CurrentUserDep,
) -> NotificationResponse:
    """
    Mark a notification as read.

    Args:
        notification_id: ID of the notification
        db: Database session
        current_user: Current authenticated user

    Returns:
        NotificationResponse: The updated notification

    Raises:
        HTTPException: If notification not found or not owned by user
    """
    notification = NotificationService.mark_as_read(
        db=db,
        notification_id=notification_id,
        user_id=current_user.id,
    )

    return NotificationResponse.model_validate(notification)


@router.post(
    "/mark-all-read",
    response_model=MessageResponse,
    summary="Mark all notifications as read",
)
async def mark_all_notifications_as_read(
    db: DatabaseDep,
    current_user: CurrentUserDep,
) -> MessageResponse:
    """
    Mark all notifications as read for the current user.

    Args:
        db: Database session
        current_user: Current authenticated user

    Returns:
        MessageResponse: Success message with count
    """
    count = NotificationService.mark_all_as_read(db=db, user_id=current_user.id)
    return MessageResponse(message=f"Marked {count} notifications as read")


@router.delete(
    "/{notification_id}",
    response_model=MessageResponse,
    summary="Delete a notification",
)
async def delete_notification(
    notification_id: UUID,
    db: DatabaseDep,
    current_user: CurrentUserDep,
) -> MessageResponse:
    """
    Delete a notification.

    Args:
        notification_id: ID of the notification
        db: Database session
        current_user: Current authenticated user

    Returns:
        MessageResponse: Success message

    Raises:
        HTTPException: If notification not found or not owned by user
    """
    NotificationService.delete_notification(
        db=db,
        notification_id=notification_id,
        user_id=current_user.id,
    )

    return MessageResponse(message="Notification deleted successfully")

