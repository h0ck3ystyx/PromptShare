"""Tests for local authentication endpoints."""

from datetime import UTC, datetime, timedelta

import pytest
from fastapi import status

from src.models.user import User
from src.models.auth_token import EmailVerificationToken, PasswordResetToken
from src.constants import UserRole
from src.services.password_service import PasswordService


class TestLocalAuth:
    """Test cases for local authentication."""

    def test_register_success(self, client, db_session):
        """Test successful user registration."""
        response = client.post(
            "/api/auth/register",
            json={
                "email": "newuser@example.com",
                "username": "newuser",
                "full_name": "New User",
                "password": "SecureP@ss123",
                "remember_me": False,
            },
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["email"] == "newuser@example.com"
        assert data["username"] == "newuser"
        
        # Verify user was created in database
        user = db_session.query(User).filter(User.email == "newuser@example.com").first()
        assert user is not None
        assert user.auth_method == "local"
        assert user.password_hash is not None
        assert user.email_verified is False

    def test_register_duplicate_email(self, client, db_session):
        """Test registration with duplicate email."""
        # Create existing user
        existing_user = User(
            email="existing@example.com",
            username="existing",
            full_name="Existing User",
            password_hash=PasswordService.hash_password("password"),
            auth_method="local",
        )
        db_session.add(existing_user)
        db_session.commit()

        response = client.post(
            "/api/auth/register",
            json={
                "email": "existing@example.com",
                "username": "newuser",
                "full_name": "New User",
                "password": "SecureP@ss123",
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "already exists" in response.json()["detail"].lower()

    def test_register_weak_password(self, client):
        """Test registration with weak password."""
        response = client.post(
            "/api/auth/register",
            json={
                "email": "user@example.com",
                "username": "user",
                "full_name": "User",
                "password": "weak",
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "password" in response.json()["detail"].lower()

    def test_verify_email_success(self, client, db_session):
        """Test successful email verification."""
        # Create user with unverified email
        user = User(
            email="user@example.com",
            username="user",
            full_name="User",
            password_hash=PasswordService.hash_password("password"),
            auth_method="local",
            email_verified=False,
        )
        db_session.add(user)
        db_session.commit()

        # Create verification token
        token = "test_verification_token"
        verification_token = EmailVerificationToken(
            user_id=user.id,
            token=token,
            expires_at=datetime.now(UTC) + timedelta(hours=24),
            used=False,
        )
        db_session.add(verification_token)
        db_session.commit()

        # Verify email via GET
        response = client.get(f"/api/auth/verify-email?token={token}")

        assert response.status_code == status.HTTP_200_OK
        
        # Verify user email is now verified
        db_session.refresh(user)
        assert user.email_verified is True

    def test_verify_email_invalid_token(self, client):
        """Test email verification with invalid token."""
        response = client.get("/api/auth/verify-email?token=invalid_token")

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_password_reset_request(self, client, db_session):
        """Test password reset request."""
        user = User(
            email="user@example.com",
            username="user",
            full_name="User",
            password_hash=PasswordService.hash_password("oldpassword"),
            auth_method="local",
        )
        db_session.add(user)
        db_session.commit()

        response = client.post(
            "/api/auth/password-reset-request",
            json={"email": "user@example.com"},
        )

        assert response.status_code == status.HTTP_200_OK
        
        # Verify reset token was created
        reset_token = db_session.query(PasswordResetToken).filter(
            PasswordResetToken.user_id == user.id
        ).first()
        assert reset_token is not None
        assert reset_token.used is False

    def test_password_reset_success(self, client, db_session):
        """Test successful password reset."""
        user = User(
            email="user@example.com",
            username="user",
            full_name="User",
            password_hash=PasswordService.hash_password("oldpassword"),
            auth_method="local",
        )
        db_session.add(user)
        db_session.commit()

        # Create reset token
        token = "test_reset_token"
        reset_token = PasswordResetToken(
            user_id=user.id,
            token=token,
            expires_at=datetime.now(UTC) + timedelta(hours=24),
            used=False,
        )
        db_session.add(reset_token)
        db_session.commit()

        old_hash = user.password_hash

        response = client.post(
            "/api/auth/password-reset",
            json={
                "token": token,
                "new_password": "NewSecureP@ss123",
            },
        )

        assert response.status_code == status.HTTP_200_OK
        
        # Verify password was changed
        db_session.refresh(user)
        assert user.password_hash != old_hash
        assert PasswordService.verify_password("NewSecureP@ss123", user.password_hash)

    def test_login_local_auth(self, client, db_session):
        """Test login with local authentication."""
        password = "testpassword123"
        user = User(
            email="localuser@example.com",
            username="localuser",
            full_name="Local User",
            password_hash=PasswordService.hash_password(password),
            auth_method="local",
            is_active=True,
        )
        db_session.add(user)
        db_session.commit()

        response = client.post(
            "/api/auth/login",
            data={"username": "localuser", "password": password},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

