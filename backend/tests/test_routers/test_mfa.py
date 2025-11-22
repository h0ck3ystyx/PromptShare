"""Tests for MFA endpoints."""

from datetime import UTC, datetime, timedelta
from unittest.mock import patch, AsyncMock

import pytest
from fastapi import status

from src.models.user import User
from src.models.auth_token import MFACode
from src.constants import UserRole
from src.services.password_service import PasswordService


class TestMFA:
    """Test cases for MFA functionality."""

    def test_mfa_enroll_success(self, client, db_session):
        """Test successful MFA enrollment."""
        password = "testpassword123"
        user = User(
            email="user@example.com",
            username="user",
            full_name="User",
            password_hash=PasswordService.hash_password(password),
            auth_method="local",
            mfa_enabled=False,
            is_active=True,
        )
        db_session.add(user)
        db_session.commit()

        # Get token
        login_response = client.post(
            "/api/auth/login",
            data={"username": "user", "password": password},
        )
        token = login_response.json()["access_token"]

        response = client.post(
            "/api/auth/mfa/enroll",
            json={"password": password},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == status.HTTP_200_OK
        
        db_session.refresh(user)
        assert user.mfa_enabled is True

    def test_mfa_enroll_wrong_password(self, client, db_session):
        """Test MFA enrollment with wrong password."""
        password = "testpassword123"
        user = User(
            email="user@example.com",
            username="user",
            full_name="User",
            password_hash=PasswordService.hash_password(password),
            auth_method="local",
            is_active=True,
        )
        db_session.add(user)
        db_session.commit()

        login_response = client.post(
            "/api/auth/login",
            data={"username": "user", "password": password},
        )
        token = login_response.json()["access_token"]

        response = client.post(
            "/api/auth/mfa/enroll",
            json={"password": "wrongpassword"},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @patch("src.services.mfa_service.EmailService.send_email")
    def test_mfa_verify_success(self, mock_send_email, client, db_session):
        """Test successful MFA verification."""
        mock_send_email.return_value = True
        
        password = "testpassword123"
        user = User(
            email="user@example.com",
            username="user",
            full_name="User",
            password_hash=PasswordService.hash_password(password),
            auth_method="local",
            mfa_enabled=True,
            is_active=True,
        )
        db_session.add(user)
        db_session.commit()

        # Login (should return pending MFA token)
        login_response = client.post(
            "/api/auth/login",
            data={"username": "user", "password": password},
        )
        
        assert login_response.status_code == status.HTTP_200_OK
        data = login_response.json()
        assert data["mfa_required"] is True
        pending_token = data["access_token"]

        # Create MFA code
        mfa_code = "123456"
        mfa_code_obj = MFACode(
            user_id=user.id,
            code=mfa_code,
            expires_at=datetime.now(UTC) + timedelta(minutes=10),
            used=False,
        )
        db_session.add(mfa_code_obj)
        db_session.commit()

        # Verify MFA
        verify_response = client.post(
            "/api/auth/mfa/verify",
            json={
                "pending_token": pending_token,
                "code": mfa_code,
                "remember_device": False,
            },
        )

        assert verify_response.status_code == status.HTTP_200_OK
        verify_data = verify_response.json()
        assert "access_token" in verify_data
        assert verify_data["mfa_required"] is False

    def test_mfa_verify_invalid_code(self, client, db_session):
        """Test MFA verification with invalid code."""
        password = "testpassword123"
        user = User(
            email="user@example.com",
            username="user",
            full_name="User",
            password_hash=PasswordService.hash_password(password),
            auth_method="local",
            mfa_enabled=True,
            is_active=True,
        )
        db_session.add(user)
        db_session.commit()

        # Login to get pending token
        login_response = client.post(
            "/api/auth/login",
            data={"username": "user", "password": password},
        )
        pending_token = login_response.json()["access_token"]

        # Try to verify with wrong code
        verify_response = client.post(
            "/api/auth/mfa/verify",
            json={
                "pending_token": pending_token,
                "code": "000000",
                "remember_device": False,
            },
        )

        assert verify_response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_mfa_disable_success(self, client, db_session):
        """Test successful MFA disable."""
        password = "testpassword123"
        user = User(
            email="user@example.com",
            username="user",
            full_name="User",
            password_hash=PasswordService.hash_password(password),
            auth_method="local",
            mfa_enabled=True,
            is_active=True,
        )
        db_session.add(user)
        db_session.commit()

        login_response = client.post(
            "/api/auth/login",
            data={"username": "user", "password": password},
        )
        token = login_response.json()["access_token"]

        response = client.post(
            "/api/auth/mfa/disable",
            json={"password": password},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == status.HTTP_200_OK
        
        db_session.refresh(user)
        assert user.mfa_enabled is False

