"""Tests for notification router endpoints."""

from uuid import uuid4

from fastapi import status

from src.constants import NotificationType, UserRole
from src.models.notification import Notification
from src.models.prompt import Prompt
from src.models.user import User
from src.services.auth_service import AuthService
from src.services.notification_service import NotificationService


class TestNotificationRouter:
    """Test cases for notification router."""

    def get_auth_headers(self, client, db_session, user_role=UserRole.MEMBER, suffix=""):
        """Helper to get auth headers for a user."""
        import uuid
        unique_id = str(uuid.uuid4())[:8]
        user = User(
            username=f"testuser_{user_role.value}_{unique_id}{suffix}",
            email=f"testuser_{user_role.value}_{unique_id}{suffix}@company.com",
            full_name=f"Test User {user_role.value}",
            role=user_role,
        )
        db_session.add(user)
        db_session.commit()

        token = AuthService.create_access_token(user.id)
        return {"Authorization": f"Bearer {token}"}, user

    def test_get_notifications_empty(self, client, db_session):
        """Test getting notifications when none exist."""
        headers, user = self.get_auth_headers(client, db_session)

        response = client.get("/api/notifications", headers=headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total"] == 0
        assert len(data["items"]) == 0

    def test_get_notifications_with_data(self, client, db_session):
        """Test getting notifications with data."""
        headers, user = self.get_auth_headers(client, db_session)

        # Create notifications
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

        response = client.get("/api/notifications", headers=headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total"] == 2
        assert len(data["items"]) == 2

    def test_get_notifications_unread_only(self, client, db_session):
        """Test getting only unread notifications."""
        headers, user = self.get_auth_headers(client, db_session)

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
        response = client.get("/api/notifications?unread_only=true", headers=headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total"] == 1
        assert len(data["items"]) == 1
        assert data["items"][0]["is_read"] is False

    def test_get_notifications_pagination(self, client, db_session):
        """Test pagination for notifications."""
        headers, user = self.get_auth_headers(client, db_session)

        # Create multiple notifications
        for i in range(5):
            NotificationService.create_notification(
                db=db_session,
                user_id=user.id,
                notification_type=NotificationType.NEW_PROMPT,
                message=f"Notification {i}",
            )

        # Get first page
        response1 = client.get("/api/notifications?page=1&page_size=2", headers=headers)
        assert response1.status_code == status.HTTP_200_OK
        data1 = response1.json()
        assert data1["total"] == 5
        assert len(data1["items"]) == 2

        # Get second page
        response2 = client.get("/api/notifications?page=2&page_size=2", headers=headers)
        assert response2.status_code == status.HTTP_200_OK
        data2 = response2.json()
        assert data2["total"] == 5
        assert len(data2["items"]) == 2

    def test_get_unread_count(self, client, db_session):
        """Test getting unread notification count."""
        headers, user = self.get_auth_headers(client, db_session)

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
        response = client.get("/api/notifications/unread-count", headers=headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["unread_count"] == 1

    def test_mark_notification_as_read(self, client, db_session):
        """Test marking a notification as read."""
        headers, user = self.get_auth_headers(client, db_session)

        notification = NotificationService.create_notification(
            db=db_session,
            user_id=user.id,
            notification_type=NotificationType.NEW_PROMPT,
            message="Test notification",
        )

        response = client.patch(
            f"/api/notifications/{notification.id}/read",
            headers=headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["is_read"] is True

    def test_mark_notification_as_read_not_found(self, client, db_session):
        """Test marking a non-existent notification as read."""
        headers, _ = self.get_auth_headers(client, db_session)

        response = client.patch(
            f"/api/notifications/{uuid4()}/read",
            headers=headers,
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_mark_notification_as_read_unauthorized(self, client, db_session):
        """Test marking another user's notification as read."""
        headers1, user1 = self.get_auth_headers(client, db_session, suffix="_1")
        headers2, user2 = self.get_auth_headers(client, db_session, suffix="_2")

        notification = NotificationService.create_notification(
            db=db_session,
            user_id=user1.id,
            notification_type=NotificationType.NEW_PROMPT,
            message="Test notification",
        )

        response = client.patch(
            f"/api/notifications/{notification.id}/read",
            headers=headers2,
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_mark_all_as_read(self, client, db_session):
        """Test marking all notifications as read."""
        headers, user = self.get_auth_headers(client, db_session)

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
        response = client.post("/api/notifications/mark-all-read", headers=headers)

        assert response.status_code == status.HTTP_200_OK
        assert "marked" in response.json()["message"].lower()

        # Verify all are read
        response2 = client.get("/api/notifications?unread_only=true", headers=headers)
        data = response2.json()
        assert data["total"] == 0

    def test_delete_notification(self, client, db_session):
        """Test deleting a notification."""
        headers, user = self.get_auth_headers(client, db_session)

        notification = NotificationService.create_notification(
            db=db_session,
            user_id=user.id,
            notification_type=NotificationType.NEW_PROMPT,
            message="Test notification",
        )

        response = client.delete(
            f"/api/notifications/{notification.id}",
            headers=headers,
        )

        assert response.status_code == status.HTTP_200_OK

        # Verify deleted
        response2 = client.get("/api/notifications", headers=headers)
        data = response2.json()
        assert data["total"] == 0

    def test_delete_notification_unauthorized(self, client, db_session):
        """Test deleting another user's notification."""
        headers1, user1 = self.get_auth_headers(client, db_session, suffix="_1")
        headers2, user2 = self.get_auth_headers(client, db_session, suffix="_2")

        notification = NotificationService.create_notification(
            db=db_session,
            user_id=user1.id,
            notification_type=NotificationType.NEW_PROMPT,
            message="Test notification",
        )

        response = client.delete(
            f"/api/notifications/{notification.id}",
            headers=headers2,
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_notifications_requires_auth(self, client, db_session):
        """Test that getting notifications requires authentication."""
        response = client.get("/api/notifications")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_mark_notification_as_read_requires_auth(self, client, db_session):
        """Test that marking notification as read requires authentication."""
        response = client.patch(f"/api/notifications/{uuid4()}/read")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

