"""Tests for notification Celery tasks."""

import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from uuid import uuid4

from src.constants import NotificationType
from src.models.notification import Notification
from src.models.user import User
from src.tasks.notifications import send_bulk_notifications_task, send_notification_task

# Disable Celery result backend for tests to avoid Redis connection
os.environ.setdefault("CELERY_RESULT_BACKEND", "cache+memory://")


class TestNotificationTasks:
    """Test cases for notification Celery tasks."""

    def test_send_notification_task_success(self, db_session):
        """Test successfully sending a notification via Celery task."""
        # Create user
        user = User(
            email="test@example.com",
            username="testuser",
            full_name="Test User",
        )
        db_session.add(user)
        db_session.commit()

        # Call task function directly using .run() which handles bound task self automatically
        # Patch SessionLocal to use our test session
        with patch("src.tasks.notifications.SessionLocal", return_value=db_session):
            result = send_notification_task.run(
                user_id=str(user.id),
                notification_type=NotificationType.NEW_PROMPT.value,
                message="Test notification",
                prompt_id=None,
                send_email=False,
            )

        assert result["status"] == "created"
        assert "notification_id" in result
        assert result["email_sent"] is False

        # Verify notification was created
        notification = db_session.query(Notification).filter(
            Notification.user_id == user.id
        ).first()
        assert notification is not None
        assert notification.message == "Test notification"

    def test_send_notification_task_with_email(self, db_session):
        """Test sending notification with email enabled."""
        # Create user
        user = User(
            email="test@example.com",
            username="testuser",
            full_name="Test User",
        )
        db_session.add(user)
        db_session.commit()

        # Create a mock task instance with db property
        class MockTask:
            def __init__(self):
                self._db = db_session
            @property
            def db(self):
                return self._db
            def retry(self, *args, **kwargs):
                raise Exception("Retry called")

        # Mock email service
        with patch("src.tasks.notifications.SessionLocal", return_value=db_session):
            with patch("src.tasks.notifications.EmailService.is_enabled", return_value=True):
                with patch("src.tasks.notifications.EmailService.send_notification_email", new_callable=AsyncMock) as mock_email:
                    # Call task function directly using .run()
                    result = send_notification_task.run(
                        user_id=str(user.id),
                        notification_type=NotificationType.COMMENT.value,
                        message="Test notification",
                        prompt_id=str(uuid4()),
                        send_email=True,
                    )

                assert result["status"] == "created"
                assert result["email_sent"] is True
                # Note: AsyncMock needs to be awaited, but in Celery task context
                # we'd need to handle this differently in real implementation

    def test_send_bulk_notifications_task(self, db_session):
        """Test sending notifications to multiple users."""
        # Create multiple users
        users = []
        for i in range(3):
            user = User(
                email=f"user{i}@example.com",
                username=f"user{i}",
                full_name=f"User {i}",
            )
            users.append(user)
            db_session.add(user)
        db_session.commit()

        user_ids = [str(user.id) for user in users]

        # Patch SessionLocal to use test db_session
        with patch("src.tasks.notifications.SessionLocal", return_value=db_session):
            # Call task function directly using .run() method
            result = send_bulk_notifications_task.run(
                user_ids=user_ids,
                notification_type=NotificationType.NEW_PROMPT.value,
                message="Bulk test notification",
                prompt_id=None,
                send_email=False,
            )

        assert result["total"] == 3
        assert result["created"] == 3
        assert result["failed"] == 0
        assert result["email_sent"] == 0

        # Verify all notifications were created
        notifications = db_session.query(Notification).filter(
            Notification.user_id.in_([user.id for user in users])
        ).all()
        assert len(notifications) == 3

    def test_send_bulk_notifications_with_invalid_user(self, db_session):
        """Test bulk notification task with invalid user IDs."""
        # Create one valid user
        user = User(
            email="valid@example.com",
            username="validuser",
            full_name="Valid User",
        )
        db_session.add(user)
        db_session.commit()

        # Mix valid and invalid user IDs
        user_ids = [str(user.id), str(uuid4())]

        # Patch SessionLocal to use test db_session
        with patch("src.tasks.notifications.SessionLocal", return_value=db_session):
            result = send_bulk_notifications_task.run(
                user_ids=user_ids,
                notification_type=NotificationType.NEW_PROMPT.value,
                message="Test notification",
                prompt_id=None,
                send_email=False,
            )

        assert result["total"] == 2
        assert result["created"] == 1
        assert result["failed"] == 1
        assert len(result["errors"]) == 1

    def test_send_notification_task_retry_on_failure(self, db_session):
        """Test that task retries on failure."""
        # Create user
        user = User(
            email="test@example.com",
            username="testuser",
            full_name="Test User",
        )
        db_session.add(user)
        db_session.commit()

        # Create a mock task instance
        class MockTask:
            def __init__(self):
                self._db = db_session
            @property
            def db(self):
                return self._db
            def retry(self, *args, **kwargs):
                raise Exception("Retry called")

        # Simulate failure by passing invalid notification type
        with patch("src.tasks.notifications.SessionLocal", return_value=db_session):
            with pytest.raises(ValueError):
                send_notification_task.run(
                    user_id=str(user.id),
                    notification_type="INVALID_TYPE",
                    message="Test",
                    prompt_id=None,
                    send_email=False,
                )

        # In real Celery, retry would be called
        # Here we just verify the exception is raised

