"""Tests for authentication service."""

import ldap
import pytest
from unittest.mock import Mock, patch
from uuid import uuid4

from src.models.user import User
from src.services.auth_service import AuthService
from src.constants import UserRole


class TestAuthService:
    """Test cases for AuthService."""

    @patch("src.services.auth_service.ldap")
    def test_authenticate_ldap_success(self, mock_ldap):
        """Test successful LDAP authentication."""
        # Mock admin LDAP connection (for search)
        mock_admin_conn = Mock()
        # Mock user LDAP connection (for user bind)
        mock_user_conn = Mock()
        
        # Set up side_effect to return different connections for admin and user
        mock_ldap.initialize.side_effect = [mock_admin_conn, mock_user_conn]
        
        # Mock admin connection search
        mock_admin_conn.search_s.return_value = [
            (
                "CN=testuser,DC=company,DC=com",
                {
                    "mail": [b"testuser@company.com"],
                    "displayName": [b"Test User"],
                },
            )
        ]
        
        # Mock user connection bind (should succeed)
        mock_user_conn.simple_bind_s.return_value = None

        result = AuthService.authenticate_ldap("testuser", "password")

        assert result is not None
        assert result["username"] == "testuser"
        assert result["email"] == "testuser@company.com"
        assert result["full_name"] == "Test User"
        
        # Verify admin connection was used for search
        mock_admin_conn.search_s.assert_called_once()
        # Verify user connection was used for bind
        mock_user_conn.simple_bind_s.assert_called_once()

    @patch("src.services.auth_service.ldap")
    def test_authenticate_ldap_invalid_credentials(self, mock_ldap):
        """Test LDAP authentication with invalid credentials."""
        # Mock admin LDAP connection (for search)
        mock_admin_conn = Mock()
        # Mock user LDAP connection (for user bind)
        mock_user_conn = Mock()
        
        # Set up side_effect to return different connections
        mock_ldap.initialize.side_effect = [mock_admin_conn, mock_user_conn]
        
        # Mock admin connection search (finds user)
        mock_admin_conn.search_s.return_value = [
            ("CN=testuser,DC=company,DC=com", {})
        ]
        
        # Mock user connection bind (raises INVALID_CREDENTIALS)
        mock_user_conn.simple_bind_s.side_effect = ldap.INVALID_CREDENTIALS

        result = AuthService.authenticate_ldap("testuser", "wrongpassword")

        assert result is None
        
        # Verify admin connection was used for search
        mock_admin_conn.search_s.assert_called_once()
        # Verify user connection was used for bind
        mock_user_conn.simple_bind_s.assert_called_once()

    def test_get_or_create_user_new_user(self, db_session):
        """Test creating a new user from LDAP info."""
        ldap_user_info = {
            "username": "newuser",
            "email": "newuser@company.com",
            "full_name": "New User",
        }

        user = AuthService.get_or_create_user(db_session, ldap_user_info)

        assert user.id is not None
        assert user.username == "newuser"
        assert user.email == "newuser@company.com"
        assert user.full_name == "New User"
        assert user.role == UserRole.MEMBER
        assert user.is_active is True

    def test_get_or_create_user_existing_user(self, db_session):
        """Test getting existing user from LDAP info."""
        # Create existing user
        existing_user = User(
            username="existinguser",
            email="existinguser@company.com",
            full_name="Existing User",
            role=UserRole.MEMBER,
        )
        db_session.add(existing_user)
        db_session.commit()

        ldap_user_info = {
            "username": "existinguser",
            "email": "existinguser@company.com",
            "full_name": "Existing User",
        }

        user = AuthService.get_or_create_user(db_session, ldap_user_info)

        assert user.id == existing_user.id
        assert user.username == "existinguser"

    @patch("src.services.auth_service.ldap")
    def test_authenticate_ldap_connection_failure(self, mock_ldap):
        """Test LDAP authentication when connection initialization fails."""
        # Mock ldap.initialize to raise an exception
        mock_ldap.initialize.side_effect = Exception("Connection failed")

        # Should return None gracefully without raising UnboundLocalError
        result = AuthService.authenticate_ldap("testuser", "password")

        assert result is None

    @patch("src.services.auth_service.ldap")
    def test_authenticate_ldap_admin_bind_failure(self, mock_ldap):
        """Test LDAP authentication when admin bind fails."""
        mock_admin_conn = Mock()
        mock_ldap.initialize.return_value = mock_admin_conn
        # Mock admin bind to fail
        mock_admin_conn.simple_bind_s.side_effect = Exception("Bind failed")

        # Should return None gracefully
        result = AuthService.authenticate_ldap("testuser", "password")

        assert result is None
        # Verify unbind was called if connection was created
        mock_admin_conn.unbind.assert_called_once()

    @patch("src.services.auth_service.ldap")
    def test_authenticate_ldap_user_connection_failure(self, mock_ldap):
        """Test LDAP authentication when user connection initialization fails."""
        mock_admin_conn = Mock()
        # First call succeeds (admin), second call fails (user)
        mock_ldap.initialize.side_effect = [mock_admin_conn, Exception("User connection failed")]
        
        mock_admin_conn.search_s.return_value = [
            ("CN=testuser,DC=company,DC=com", {})
        ]

        # Should return None gracefully without raising UnboundLocalError
        result = AuthService.authenticate_ldap("testuser", "password")

        assert result is None
        # Verify admin connection was cleaned up
        mock_admin_conn.unbind.assert_called_once()

    def test_create_access_token(self):
        """Test JWT token creation."""
        user_id = uuid4()
        token = AuthService.create_access_token(user_id)

        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

