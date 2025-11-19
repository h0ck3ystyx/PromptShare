"""Notification service for managing user notifications."""

from typing import Optional
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from src.constants import NotificationType
from src.models.notification import Notification
from src.models.user import User


class NotificationService:
    """Service for handling notification operations."""

    @staticmethod
    def create_notification(
        db: Session,
        user_id: UUID,
        notification_type: NotificationType,
        message: str,
        prompt_id: Optional[UUID] = None,
    ) -> Notification:
        """
        Create a notification for a user.

        Args:
            db: Database session
            user_id: ID of the user to notify
            notification_type: Type of notification
            message: Notification message
            prompt_id: Optional prompt ID related to the notification

        Returns:
            Notification: The created notification
        """
        notification = Notification(
            user_id=user_id,
            type=notification_type,
            message=message,
            prompt_id=prompt_id,
            is_read=False,
        )
        db.add(notification)
        db.commit()
        db.refresh(notification)

        return notification

    @staticmethod
    def get_user_notifications(
        db: Session,
        user_id: UUID,
        unread_only: bool = False,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[Notification], int]:
        """
        Get notifications for a user.

        Args:
            db: Database session
            user_id: ID of the user
            unread_only: If True, only return unread notifications
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            tuple: (list of notifications, total count)
        """
        query = db.query(Notification).filter(Notification.user_id == user_id)

        if unread_only:
            query = query.filter(Notification.is_read == False)  # noqa: E712

        # Get total count before pagination
        total = query.count()

        # Apply ordering and pagination
        notifications = (
            query.order_by(Notification.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

        return notifications, total

    @staticmethod
    def mark_as_read(
        db: Session,
        notification_id: UUID,
        user_id: UUID,
    ) -> Notification:
        """
        Mark a notification as read.

        Args:
            db: Database session
            notification_id: ID of the notification
            user_id: ID of the user (for authorization)

        Returns:
            Notification: The updated notification

        Raises:
            HTTPException: If notification not found or not owned by user
        """
        notification = db.query(Notification).filter(Notification.id == notification_id).first()

        if not notification:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notification not found",
            )

        if notification.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to mark this notification as read",
            )

        notification.is_read = True
        db.commit()
        db.refresh(notification)

        return notification

    @staticmethod
    def mark_all_as_read(
        db: Session,
        user_id: UUID,
    ) -> int:
        """
        Mark all notifications as read for a user.

        Args:
            db: Database session
            user_id: ID of the user

        Returns:
            int: Number of notifications marked as read
        """
        updated = (
            db.query(Notification)
            .filter(Notification.user_id == user_id, Notification.is_read == False)  # noqa: E712
            .update({"is_read": True})
        )
        db.commit()

        return updated

    @staticmethod
    def get_unread_count(
        db: Session,
        user_id: UUID,
    ) -> int:
        """
        Get count of unread notifications for a user.

        Args:
            db: Database session
            user_id: ID of the user

        Returns:
            int: Number of unread notifications
        """
        return (
            db.query(Notification)
            .filter(Notification.user_id == user_id, Notification.is_read == False)  # noqa: E712
            .count()
        )

    @staticmethod
    def delete_notification(
        db: Session,
        notification_id: UUID,
        user_id: UUID,
    ) -> None:
        """
        Delete a notification.

        Args:
            db: Database session
            notification_id: ID of the notification
            user_id: ID of the user (for authorization)

        Raises:
            HTTPException: If notification not found or not owned by user
        """
        notification = db.query(Notification).filter(Notification.id == notification_id).first()

        if not notification:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notification not found",
            )

        if notification.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to delete this notification",
            )

        db.delete(notification)
        db.commit()

