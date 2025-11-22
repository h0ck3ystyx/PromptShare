"""Tests for authentication router endpoints."""

import ldap
from unittest.mock import patch

import pytest
from fastapi import status

from src.models.user import User
from src.constants import UserRole


class TestAuthRouter:
    """Test cases for authentication router."""

    @patch("src.routers.auth.run_in_threadpool")
    @patch("src.routers.auth.AuthService")
    def test_login_inactive_user_rejected(self, mock_auth_service, mock_run_in_threadpool, client, db_session):
        """Test that inactive users cannot log in."""
        # Mock LDAP authentication success
        ldap_user_info = {
            "username": "inactiveuser",
            "email": "inactiveuser@company.com",
            "full_name": "Inactive User",
        }
        mock_run_in_threadpool.return_value = ldap_user_info

        # Create inactive user in database
        inactive_user = User(
            username="inactiveuser",
            email="inactiveuser@company.com",
            full_name="Inactive User",
            role=UserRole.MEMBER,
            is_active=False,
        )
        db_session.add(inactive_user)
        db_session.commit()

        # Mock get_or_create_user to return the inactive user
        mock_auth_service.get_or_create_user.return_value = inactive_user

        # Attempt to log in
        response = client.post(
            "/api/auth/login",
            data={"username": "inactiveuser", "password": "password"},
        )

        # Should be rejected with 403 Forbidden
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "inactive" in response.json()["detail"].lower()

        # Verify token was not created
        mock_auth_service.create_access_token.assert_not_called()

    @patch("src.routers.auth.run_in_threadpool")
    @patch("src.routers.auth.AuthService")
    @patch("src.routers.auth.SessionService")
    def test_login_active_user_succeeds(self, mock_session_service, mock_auth_service, mock_run_in_threadpool, client, db_session):
        """Test that active users can log in successfully."""
        # Mock LDAP authentication success
        ldap_user_info = {
            "username": "activeuser",
            "email": "activeuser@company.com",
            "full_name": "Active User",
        }
        mock_run_in_threadpool.return_value = ldap_user_info

        # Create active user in database
        active_user = User(
            username="activeuser",
            email="activeuser@company.com",
            full_name="Active User",
            role=UserRole.MEMBER,
            is_active=True,
        )
        db_session.add(active_user)
        db_session.commit()

        # Mock get_or_create_user to return the active user
        mock_auth_service.get_or_create_user.return_value = active_user
        # Mock token creation
        mock_auth_service.create_access_token.return_value = "test_token_123"
        # Mock session creation
        from unittest.mock import MagicMock
        mock_session = MagicMock()
        mock_session_service.create_session.return_value = mock_session

        # Attempt to log in
        response = client.post(
            "/api/auth/login",
            data={"username": "activeuser", "password": "password"},
        )

        # Should succeed
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["access_token"] == "test_token_123"
        assert response.json()["token_type"] == "bearer"

        # Verify token was created
        mock_auth_service.create_access_token.assert_called_once_with(active_user.id)
        # Verify session was created
        mock_session_service.create_session.assert_called_once()

