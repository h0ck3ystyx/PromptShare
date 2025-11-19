"""Tests for user router security fixes."""

import pytest
from fastapi import status

from src.constants import UserRole
from src.models.user import User
from src.services.auth_service import AuthService


class TestUserRouterFixes:
    """Test cases for user router security fixes."""

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

    def test_user_can_view_own_stats(self, client, db_session):
        """Test that user can view their own statistics."""
        user = User(
            username="testuser_stats_own",
            email="testuser_stats_own@company.com",
            full_name="Test User",
            role=UserRole.MEMBER,
        )
        db_session.add(user)
        db_session.commit()

        token = AuthService.create_access_token(user.id)
        headers = {"Authorization": f"Bearer {token}"}

        response = client.get(f"/api/users/{user.id}/stats", headers=headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "prompt_count" in data

    def test_admin_can_view_any_user_stats(self, client, db_session):
        """Test that admin can view any user's statistics."""
        admin = User(
            username="admin_stats",
            email="admin_stats@company.com",
            full_name="Admin User",
            role=UserRole.ADMIN,
        )
        member = User(
            username="member_stats",
            email="member_stats@company.com",
            full_name="Member User",
            role=UserRole.MEMBER,
        )
        db_session.add_all([admin, member])
        db_session.commit()

        token = AuthService.create_access_token(admin.id)
        admin_headers = {"Authorization": f"Bearer {token}"}

        response = client.get(f"/api/users/{member.id}/stats", headers=admin_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "prompt_count" in data

    def test_moderator_can_view_any_user_stats(self, client, db_session):
        """Test that moderator can view any user's statistics."""
        moderator = User(
            username="moderator_stats",
            email="moderator_stats@company.com",
            full_name="Moderator User",
            role=UserRole.MODERATOR,
        )
        member = User(
            username="member_stats2",
            email="member_stats2@company.com",
            full_name="Member User",
            role=UserRole.MEMBER,
        )
        db_session.add_all([moderator, member])
        db_session.commit()

        token = AuthService.create_access_token(moderator.id)
        moderator_headers = {"Authorization": f"Bearer {token}"}

        response = client.get(f"/api/users/{member.id}/stats", headers=moderator_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "prompt_count" in data

    def test_member_cannot_view_other_user_stats(self, client, db_session):
        """Test that member cannot view other user's statistics."""
        member1 = User(
            username="member1_stats",
            email="member1_stats@company.com",
            full_name="Member One",
            role=UserRole.MEMBER,
        )
        member2 = User(
            username="member2_stats",
            email="member2_stats@company.com",
            full_name="Member Two",
            role=UserRole.MEMBER,
        )
        db_session.add_all([member1, member2])
        db_session.commit()

        token = AuthService.create_access_token(member1.id)
        member1_headers = {"Authorization": f"Bearer {token}"}

        response = client.get(f"/api/users/{member2.id}/stats", headers=member1_headers)

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "Not authorized" in response.json()["detail"]

    def test_admin_cannot_change_own_role_via_me_endpoint(self, client, db_session):
        """Test that admin cannot change own role through /api/users/me."""
        admin = User(
            username="admin_me",
            email="admin_me@company.com",
            full_name="Admin User",
            role=UserRole.ADMIN,
        )
        db_session.add(admin)
        db_session.commit()

        token = AuthService.create_access_token(admin.id)
        admin_headers = {"Authorization": f"Bearer {token}"}

        update_data = {"role": "member"}

        response = client.put("/api/users/me", json=update_data, headers=admin_headers)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Cannot change your own role" in response.json()["detail"]

    def test_admin_cannot_deactivate_self_via_me_endpoint(self, client, db_session):
        """Test that admin cannot deactivate themselves through /api/users/me."""
        admin = User(
            username="admin_deactivate_me",
            email="admin_deactivate_me@company.com",
            full_name="Admin User",
            role=UserRole.ADMIN,
            is_active=True,
        )
        db_session.add(admin)
        db_session.commit()

        token = AuthService.create_access_token(admin.id)
        admin_headers = {"Authorization": f"Bearer {token}"}

        update_data = {"is_active": False}

        response = client.put("/api/users/me", json=update_data, headers=admin_headers)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Cannot deactivate your own account" in response.json()["detail"]

