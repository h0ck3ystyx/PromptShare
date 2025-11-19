"""Tests for notification service."""

from uuid import uuid4

import pytest
from fastapi import status

from src.constants import NotificationType
from src.models.notification import Notification
from src.models.prompt import Prompt
from src.models.user import User
from src.services.notification_service import NotificationService


def test_create_notification(db_session):
    """Test creating a notification."""
    user = User(
        email="test@example.com",
        username="testuser",
        full_name="Test User",
    )
    db_session.add(user)
    db_session.commit()

    notification = NotificationService.create_notification(
        db=db_session,
        user_id=user.id,
        notification_type=NotificationType.NEW_PROMPT,
        message="Test notification",
    )

    assert notification is not None
    assert notification.user_id == user.id
    assert notification.type == NotificationType.NEW_PROMPT
    assert notification.message == "Test notification"
    assert notification.is_read is False

    # Verify in database
    db_notification = db_session.query(Notification).filter(Notification.id == notification.id).first()
    assert db_notification is not None
    assert db_notification.message == "Test notification"


def test_create_notification_with_prompt(db_session):
    """Test creating a notification with a prompt ID."""
    user = User(
        email="test@example.com",
        username="testuser",
        full_name="Test User",
    )
    db_session.add(user)
    db_session.commit()

    prompt = Prompt(
        title="Test Prompt",
        content="Test content",
        author_id=user.id,
        platform_tags=[],
    )
    db_session.add(prompt)
    db_session.commit()

    notification = NotificationService.create_notification(
        db=db_session,
        user_id=user.id,
        notification_type=NotificationType.COMMENT,
        message="New comment",
        prompt_id=prompt.id,
    )

    assert notification.prompt_id == prompt.id


def test_get_user_notifications(db_session):
    """Test getting notifications for a user."""
    user = User(
        email="test@example.com",
        username="testuser",
        full_name="Test User",
    )
    db_session.add(user)
    db_session.commit()

    # Create multiple notifications
    NotificationService.create_notification(
        db=db_session,
        user_id=user.id,
        notification_type=NotificationType.NEW_PROMPT,
        message="Notification 1",
    )
    NotificationService.create_notification(
        db=db_session,
        user_id=user.id,
        notification_type=NotificationType.COMMENT,
        message="Notification 2",
    )
    NotificationService.create_notification(
        db=db_session,
        user_id=user.id,
        notification_type=NotificationType.UPDATE,
        message="Notification 3",
    )

    # Get all notifications
    notifications, total = NotificationService.get_user_notifications(
        db=db_session,
        user_id=user.id,
    )

    assert total == 3
    assert len(notifications) == 3


def test_get_user_notifications_unread_only(db_session):
    """Test getting only unread notifications."""
    user = User(
        email="test@example.com",
        username="testuser",
        full_name="Test User",
    )
    db_session.add(user)
    db_session.commit()

    # Create notifications
    notif1 = NotificationService.create_notification(
        db=db_session,
        user_id=user.id,
        notification_type=NotificationType.NEW_PROMPT,
        message="Unread 1",
    )
    NotificationService.create_notification(
        db=db_session,
        user_id=user.id,
        notification_type=NotificationType.COMMENT,
        message="Unread 2",
    )

    # Mark one as read
    NotificationService.mark_as_read(
        db=db_session,
        notification_id=notif1.id,
        user_id=user.id,
    )

    # Get unread only
    notifications, total = NotificationService.get_user_notifications(
        db=db_session,
        user_id=user.id,
        unread_only=True,
    )

    assert total == 1
    assert len(notifications) == 1
    assert notifications[0].id != notif1.id
    assert notifications[0].is_read is False


def test_get_user_notifications_pagination(db_session):
    """Test pagination for user notifications."""
    user = User(
        email="test@example.com",
        username="testuser",
        full_name="Test User",
    )
    db_session.add(user)
    db_session.commit()

    # Create multiple notifications
    for i in range(5):
        NotificationService.create_notification(
            db=db_session,
            user_id=user.id,
            notification_type=NotificationType.NEW_PROMPT,
            message=f"Notification {i}",
        )

    # Get first page
    page1, total = NotificationService.get_user_notifications(
        db=db_session,
        user_id=user.id,
        skip=0,
        limit=2,
    )

    assert total == 5
    assert len(page1) == 2

    # Get second page
    page2, total = NotificationService.get_user_notifications(
        db=db_session,
        user_id=user.id,
        skip=2,
        limit=2,
    )

    assert total == 5
    assert len(page2) == 2


def test_mark_as_read(db_session):
    """Test marking a notification as read."""
    user = User(
        email="test@example.com",
        username="testuser",
        full_name="Test User",
    )
    db_session.add(user)
    db_session.commit()

    notification = NotificationService.create_notification(
        db=db_session,
        user_id=user.id,
        notification_type=NotificationType.NEW_PROMPT,
        message="Test notification",
    )

    assert notification.is_read is False

    # Mark as read
    updated = NotificationService.mark_as_read(
        db=db_session,
        notification_id=notification.id,
        user_id=user.id,
    )

    assert updated.is_read is True

    # Verify in database
    db_notification = db_session.query(Notification).filter(Notification.id == notification.id).first()
    assert db_notification.is_read is True


def test_mark_as_read_not_found(db_session):
    """Test marking a non-existent notification as read."""
    user = User(
        email="test@example.com",
        username="testuser",
        full_name="Test User",
    )
    db_session.add(user)
    db_session.commit()

    with pytest.raises(Exception) as exc_info:
        NotificationService.mark_as_read(
            db=db_session,
            notification_id=uuid4(),
            user_id=user.id,
        )

    assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND


def test_mark_as_read_unauthorized(db_session):
    """Test marking another user's notification as read."""
    user1 = User(
        email="user1@example.com",
        username="user1",
        full_name="User 1",
    )
    user2 = User(
        email="user2@example.com",
        username="user2",
        full_name="User 2",
    )
    db_session.add_all([user1, user2])
    db_session.commit()

    notification = NotificationService.create_notification(
        db=db_session,
        user_id=user1.id,
        notification_type=NotificationType.NEW_PROMPT,
        message="Test notification",
    )

    with pytest.raises(Exception) as exc_info:
        NotificationService.mark_as_read(
            db=db_session,
            notification_id=notification.id,
            user_id=user2.id,
        )

    assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN


def test_mark_all_as_read(db_session):
    """Test marking all notifications as read."""
    user = User(
        email="test@example.com",
        username="testuser",
        full_name="Test User",
    )
    db_session.add(user)
    db_session.commit()

    # Create multiple notifications
    NotificationService.create_notification(
        db=db_session,
        user_id=user.id,
        notification_type=NotificationType.NEW_PROMPT,
        message="Notification 1",
    )
    NotificationService.create_notification(
        db=db_session,
        user_id=user.id,
        notification_type=NotificationType.COMMENT,
        message="Notification 2",
    )

    # Mark all as read
    count = NotificationService.mark_all_as_read(
        db=db_session,
        user_id=user.id,
    )

    assert count == 2

    # Verify all are read
    notifications, total = NotificationService.get_user_notifications(
        db=db_session,
        user_id=user.id,
        unread_only=True,
    )

    assert total == 0
    assert len(notifications) == 0


def test_get_unread_count(db_session):
    """Test getting unread notification count."""
    user = User(
        email="test@example.com",
        username="testuser",
        full_name="Test User",
    )
    db_session.add(user)
    db_session.commit()

    # Create notifications
    NotificationService.create_notification(
        db=db_session,
        user_id=user.id,
        notification_type=NotificationType.NEW_PROMPT,
        message="Unread 1",
    )
    notif2 = NotificationService.create_notification(
        db=db_session,
        user_id=user.id,
        notification_type=NotificationType.COMMENT,
        message="Unread 2",
    )

    # Mark one as read
    NotificationService.mark_as_read(
        db=db_session,
        notification_id=notif2.id,
        user_id=user.id,
    )

    # Get unread count
    count = NotificationService.get_unread_count(
        db=db_session,
        user_id=user.id,
    )

    assert count == 1


def test_delete_notification(db_session):
    """Test deleting a notification."""
    user = User(
        email="test@example.com",
        username="testuser",
        full_name="Test User",
    )
    db_session.add(user)
    db_session.commit()

    notification = NotificationService.create_notification(
        db=db_session,
        user_id=user.id,
        notification_type=NotificationType.NEW_PROMPT,
        message="Test notification",
    )

    # Delete notification
    NotificationService.delete_notification(
        db=db_session,
        notification_id=notification.id,
        user_id=user.id,
    )

    # Verify deleted
    db_notification = db_session.query(Notification).filter(Notification.id == notification.id).first()
    assert db_notification is None


def test_delete_notification_unauthorized(db_session):
    """Test deleting another user's notification."""
    user1 = User(
        email="user1@example.com",
        username="user1",
        full_name="User 1",
    )
    user2 = User(
        email="user2@example.com",
        username="user2",
        full_name="User 2",
    )
    db_session.add_all([user1, user2])
    db_session.commit()

    notification = NotificationService.create_notification(
        db=db_session,
        user_id=user1.id,
        notification_type=NotificationType.NEW_PROMPT,
        message="Test notification",
    )

    with pytest.raises(Exception) as exc_info:
        NotificationService.delete_notification(
            db=db_session,
            notification_id=notification.id,
            user_id=user2.id,
        )

    assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN

