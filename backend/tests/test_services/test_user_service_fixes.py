"""Tests for user service fixes."""

import pytest
from fastapi import HTTPException, status

from src.constants import UserRole
from src.models.user import User
from src.schemas.user import UserUpdate
from src.services.user_service import UserService


class TestUserServiceFixes:
    """Test cases for user service security fixes."""

    def test_admin_cannot_change_own_role_via_update_profile(self, db_session):
        """Test that admin cannot change own role through update_user_profile."""
        admin = User(
            username="admin_self",
            email="admin_self@company.com",
            full_name="Admin User",
            role=UserRole.ADMIN,
        )
        db_session.add(admin)
        db_session.commit()

        update_data = UserUpdate(role=UserRole.MEMBER)

        with pytest.raises(HTTPException) as exc_info:
            UserService.update_user_profile(
                db_session, admin.id, update_data, admin
            )

        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert "Cannot change your own role" in exc_info.value.detail

    def test_admin_cannot_deactivate_self_via_update_profile(self, db_session):
        """Test that admin cannot deactivate themselves through update_user_profile."""
        admin = User(
            username="admin_deactivate",
            email="admin_deactivate@company.com",
            full_name="Admin User",
            role=UserRole.ADMIN,
            is_active=True,
        )
        db_session.add(admin)
        db_session.commit()

        update_data = UserUpdate(is_active=False)

        with pytest.raises(HTTPException) as exc_info:
            UserService.update_user_profile(
                db_session, admin.id, update_data, admin
            )

        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert "Cannot deactivate your own account" in exc_info.value.detail

    def test_admin_can_change_other_user_role_via_update_profile(self, db_session):
        """Test that admin can still change other users' role through update_user_profile."""
        admin = User(
            username="admin_other",
            email="admin_other@company.com",
            full_name="Admin User",
            role=UserRole.ADMIN,
        )
        member = User(
            username="member_other",
            email="member_other@company.com",
            full_name="Member User",
            role=UserRole.MEMBER,
        )
        db_session.add_all([admin, member])
        db_session.commit()

        update_data = UserUpdate(role=UserRole.MODERATOR)

        updated = UserService.update_user_profile(
            db_session, member.id, update_data, admin
        )

        assert updated.role == UserRole.MODERATOR

