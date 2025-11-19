"""Celery tasks for notification delivery."""

import asyncio
from typing import Optional
from uuid import UUID

from celery import Task
from sqlalchemy.orm import Session

from src.celery_app import celery_app
from src.constants import NotificationType
from src.database import SessionLocal
from src.services.email_service import EmailService
from src.services.notification_service import NotificationService


class DatabaseTask(Task):
    """Celery task with database session management."""

    _db: Optional[Session] = None

    @property
    def db(self) -> Session:
        """Get or create database session."""
        if self._db is None:
            self._db = SessionLocal()
        return self._db

    def after_return(self, *args, **kwargs):
        """Close database session after task completion."""
        if self._db is not None:
            self._db.close()
            self._db = None


@celery_app.task(base=DatabaseTask, bind=True, name="notifications.send_notification")
def send_notification_task(
    self: DatabaseTask,
    user_id: str,
    notification_type: str,
    message: str,
    prompt_id: Optional[str] = None,
    send_email: bool = False,
) -> dict:
    """
    Celery task to send a notification asynchronously.

    Args:
        self: Task instance with database session
        user_id: UUID string of the user to notify
        notification_type: Notification type (NEW_PROMPT, COMMENT, UPDATE)
        message: Notification message
        prompt_id: Optional prompt ID UUID string
        send_email: Whether to also send email notification

    Returns:
        dict: Task result with notification ID and status
    """
    from uuid import UUID

    try:
        # Convert string UUIDs to UUID objects
        user_uuid = UUID(user_id)
        prompt_uuid = UUID(prompt_id) if prompt_id else None
        notif_type = NotificationType(notification_type)

        # Create notification in database
        notification = NotificationService.create_notification(
            db=self.db,
            user_id=user_uuid,
            notification_type=notif_type,
            message=message,
            prompt_id=prompt_uuid,
        )

        result = {
            "notification_id": str(notification.id),
            "status": "created",
            "email_sent": False,
        }

        # Send email if enabled
        if send_email and EmailService.is_enabled():
            try:
                # Run async email function in event loop
                asyncio.run(
                    EmailService.send_notification_email(
                        user_id=user_uuid,
                        notification_type=notif_type,
                        message=message,
                        prompt_id=prompt_uuid,
                    )
                )
                result["email_sent"] = True
            except Exception as e:
                # Log error but don't fail the task
                result["email_sent"] = False
                result["email_error"] = str(e)

        return result
    except Exception as e:
        # Task will be retried on failure
        raise self.retry(exc=e, countdown=60, max_retries=3)


@celery_app.task(name="notifications.send_bulk_notifications")
def send_bulk_notifications_task(
    user_ids: list[str],
    notification_type: str,
    message: str,
    prompt_id: Optional[str] = None,
    send_email: bool = False,
) -> dict:
    """
    Celery task to send notifications to multiple users.

    Args:
        user_ids: List of user ID UUID strings
        notification_type: Notification type
        message: Notification message
        prompt_id: Optional prompt ID UUID string
        send_email: Whether to also send email notifications

    Returns:
        dict: Task result with counts and status
    """
    from uuid import UUID

    results = {
        "total": len(user_ids),
        "created": 0,
        "failed": 0,
        "email_sent": 0,
        "errors": [],
    }

    from src.database import SessionLocal
    db = SessionLocal()
    try:
        notif_type = NotificationType(notification_type)
        prompt_uuid = UUID(prompt_id) if prompt_id else None

        for user_id_str in user_ids:
            try:
                user_uuid = UUID(user_id_str)

                # Create notification
                NotificationService.create_notification(
                    db=db,
                    user_id=user_uuid,
                    notification_type=notif_type,
                    message=message,
                    prompt_id=prompt_uuid,
                )
                results["created"] += 1

                # Send email if enabled
                if send_email and EmailService.is_enabled():
                    try:
                        # Run async email function in event loop
                        asyncio.run(
                            EmailService.send_notification_email(
                                user_id=user_uuid,
                                notification_type=notif_type,
                                message=message,
                                prompt_id=prompt_uuid,
                            )
                        )
                        results["email_sent"] += 1
                    except Exception as e:
                        results["errors"].append(f"Email error for {user_id_str}: {str(e)}")

            except Exception as e:
                results["failed"] += 1
                results["errors"].append(f"Error for {user_id_str}: {str(e)}")

        db.commit()
    finally:
        db.close()

    return results

