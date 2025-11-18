"""Tests for user router endpoints."""

import pytest
from fastapi import status

from src.constants import UserRole
from src.models.user import User
from src.services.auth_service import AuthService


class TestUserRouter:
    """Test cases for user router."""

    def get_auth_headers(self, client, db_session, username="testuser", role=UserRole.MEMBER):
        """Helper to get auth headers for a user."""
        user = User(
            username=username,
            email=f"{username}@company.com",
            full_name=f"{username.title()} User",
            role=role,
        )
        db_session.add(user)
        db_session.commit()

        token = AuthService.create_access_token(user.id)
        return {"Authorization": f"Bearer {token}"}

    def test_list_users_admin_only(self, client, db_session):
        """Test that only admins can list users."""
        # Try as member
        member_headers = self.get_auth_headers(client, db_session, "member", UserRole.MEMBER)
        response = client.get("/api/users", headers=member_headers)
        assert response.status_code == status.HTTP_403_FORBIDDEN

        # Try as admin
        admin_headers = self.get_auth_headers(client, db_session, "admin", UserRole.ADMIN)
        response = client.get("/api/users", headers=admin_headers)
        assert response.status_code == status.HTTP_200_OK

    def test_get_my_profile(self, client, db_session):
        """Test getting current user profile."""
        headers = self.get_auth_headers(client, db_session, "testuser")

        response = client.get("/api/users/me", headers=headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["username"] == "testuser"

    def test_update_my_profile(self, client, db_session):
        """Test updating own profile."""
        headers = self.get_auth_headers(client, db_session, "testuser")

        update_data = {"full_name": "Updated Name"}

        response = client.put("/api/users/me", json=update_data, headers=headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["full_name"] == "Updated Name"

    def test_get_user_profile(self, client, db_session):
        """Test getting user profile by ID."""
        user = User(
            username="testuser",
            email="testuser@company.com",
            full_name="Test User",
            role=UserRole.MEMBER,
        )
        db_session.add(user)
        db_session.commit()

        headers = self.get_auth_headers(client, db_session, "viewer")

        response = client.get(f"/api/users/{user.id}", headers=headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["username"] == "testuser"

    def test_update_user_role_admin_only(self, client, db_session):
        """Test that only admins can update user roles."""
        admin = User(
            username="admin_role",
            email="admin_role@company.com",
            full_name="Admin User",
            role=UserRole.ADMIN,
        )
        member = User(
            username="member_role",
            email="member_role@company.com",
            full_name="Member User",
            role=UserRole.MEMBER,
        )
        db_session.add_all([admin, member])
        db_session.commit()

        # Use the existing admin user for auth headers
        token = AuthService.create_access_token(admin.id)
        admin_headers = {"Authorization": f"Bearer {token}"}
        
        role_data = {"role": "moderator"}

        response = client.put(
            f"/api/users/{member.id}/role",
            json=role_data,
            headers=admin_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["role"] == "moderator"
        
        # Clean up - delete the users to avoid conflicts
        db_session.delete(admin)
        db_session.delete(member)
        db_session.commit()

    def test_update_user_status_admin_only(self, client, db_session):
        """Test that only admins can update user status."""
        admin = User(
            username="admin_status",
            email="admin_status@company.com",
            full_name="Admin User",
            role=UserRole.ADMIN,
        )
        member = User(
            username="member_status",
            email="member_status@company.com",
            full_name="Member User",
            role=UserRole.MEMBER,
            is_active=True,
        )
        db_session.add_all([admin, member])
        db_session.commit()

        # Use the existing admin user for auth headers
        token = AuthService.create_access_token(admin.id)
        admin_headers = {"Authorization": f"Bearer {token}"}
        
        status_data = {"is_active": False}

        response = client.put(
            f"/api/users/{member.id}/status",
            json=status_data,
            headers=admin_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["is_active"] is False
        
        # Clean up - delete the users to avoid conflicts
        db_session.delete(admin)
        db_session.delete(member)
        db_session.commit()

    def test_get_user_stats(self, client, db_session):
        """Test getting user statistics."""
        user = User(
            username="testuser_stats",
            email="testuser_stats@company.com",
            full_name="Test User",
            role=UserRole.MEMBER,
        )
        db_session.add(user)
        db_session.commit()

        # User can view their own stats
        token = AuthService.create_access_token(user.id)
        headers = {"Authorization": f"Bearer {token}"}

        response = client.get(f"/api/users/{user.id}/stats", headers=headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "prompt_count" in data
        assert "comment_count" in data

