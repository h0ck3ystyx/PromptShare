"""Tests for authentication service."""

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
        # Mock LDAP connection
        mock_conn = Mock()
        mock_ldap.initialize.return_value = mock_conn
        mock_conn.search_s.return_value = [
            (
                "CN=testuser,DC=company,DC=com",
                {
                    "mail": [b"testuser@company.com"],
                    "displayName": [b"Test User"],
                },
            )
        ]

        # Mock user bind
        mock_user_conn = Mock()
        mock_ldap.initialize.return_value = mock_user_conn

        result = AuthService.authenticate_ldap("testuser", "password")

        assert result is not None
        assert result["username"] == "testuser"
        assert result["email"] == "testuser@company.com"
        assert result["full_name"] == "Test User"

    @patch("src.services.auth_service.ldap")
    def test_authenticate_ldap_invalid_credentials(self, mock_ldap):
        """Test LDAP authentication with invalid credentials."""
        mock_conn = Mock()
        mock_ldap.initialize.return_value = mock_conn
        mock_conn.search_s.return_value = [
            ("CN=testuser,DC=company,DC=com", {})
        ]

        mock_user_conn = Mock()
        mock_ldap.initialize.return_value = mock_user_conn
        mock_user_conn.simple_bind_s.side_effect = Exception("INVALID_CREDENTIALS")

        result = AuthService.authenticate_ldap("testuser", "wrongpassword")

        assert result is None

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

    def test_create_access_token(self):
        """Test JWT token creation."""
        user_id = uuid4()
        token = AuthService.create_access_token(user_id)

        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

