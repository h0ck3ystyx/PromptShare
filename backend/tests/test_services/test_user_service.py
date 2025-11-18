"""Tests for user service."""

import pytest
from fastapi import HTTPException, status
from uuid import uuid4

from src.constants import UserRole
from src.models.user import User
from src.schemas.user import UserUpdate
from src.services.user_service import UserService


class TestUserService:
    """Test cases for UserService."""

    def test_get_users_with_pagination(self, db_session):
        """Test getting users with pagination."""
        # Create test users
        user1 = User(
            username="user1",
            email="user1@company.com",
            full_name="User One",
            role=UserRole.MEMBER,
        )
        user2 = User(
            username="user2",
            email="user2@company.com",
            full_name="User Two",
            role=UserRole.MEMBER,
        )
        db_session.add_all([user1, user2])
        db_session.commit()

        users, total = UserService.get_users(db_session, skip=0, limit=10)

        assert total >= 2
        assert len(users) >= 2

    def test_get_users_with_role_filter(self, db_session):
        """Test filtering users by role."""
        # Create test users
        admin = User(
            username="admin",
            email="admin@company.com",
            full_name="Admin User",
            role=UserRole.ADMIN,
        )
        member = User(
            username="member",
            email="member@company.com",
            full_name="Member User",
            role=UserRole.MEMBER,
        )
        db_session.add_all([admin, member])
        db_session.commit()

        users, total = UserService.get_users(
            db_session, skip=0, limit=10, role_filter=UserRole.ADMIN
        )

        assert all(user.role == UserRole.ADMIN for user in users)

    def test_get_user_by_id(self, db_session):
        """Test getting user by ID."""
        user = User(
            username="testuser",
            email="testuser@company.com",
            full_name="Test User",
            role=UserRole.MEMBER,
        )
        db_session.add(user)
        db_session.commit()

        found_user = UserService.get_user_by_id(db_session, user.id)

        assert found_user is not None
        assert found_user.id == user.id
        assert found_user.username == "testuser"

    def test_update_user_role_admin(self, db_session):
        """Test updating user role by admin."""
        admin = User(
            username="admin",
            email="admin@company.com",
            full_name="Admin User",
            role=UserRole.ADMIN,
        )
        member = User(
            username="member",
            email="member@company.com",
            full_name="Member User",
            role=UserRole.MEMBER,
        )
        db_session.add_all([admin, member])
        db_session.commit()

        updated = UserService.update_user_role(
            db_session, member.id, UserRole.MODERATOR, admin
        )

        assert updated.role == UserRole.MODERATOR

    def test_update_user_role_unauthorized(self, db_session):
        """Test that non-admins cannot update user roles."""
        member1 = User(
            username="member1",
            email="member1@company.com",
            full_name="Member One",
            role=UserRole.MEMBER,
        )
        member2 = User(
            username="member2",
            email="member2@company.com",
            full_name="Member Two",
            role=UserRole.MEMBER,
        )
        db_session.add_all([member1, member2])
        db_session.commit()

        with pytest.raises(HTTPException) as exc_info:
            UserService.update_user_role(
                db_session, member2.id, UserRole.MODERATOR, member1
            )

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN

    def test_update_user_status(self, db_session):
        """Test activating/deactivating user."""
        admin = User(
            username="admin",
            email="admin@company.com",
            full_name="Admin User",
            role=UserRole.ADMIN,
        )
        member = User(
            username="member",
            email="member@company.com",
            full_name="Member User",
            role=UserRole.MEMBER,
            is_active=True,
        )
        db_session.add_all([admin, member])
        db_session.commit()

        updated = UserService.update_user_status(
            db_session, member.id, False, admin
        )

        assert updated.is_active is False

    def test_update_user_profile_own(self, db_session):
        """Test user updating their own profile."""
        user = User(
            username="testuser",
            email="testuser@company.com",
            full_name="Test User",
            role=UserRole.MEMBER,
        )
        db_session.add(user)
        db_session.commit()

        update_data = UserUpdate(full_name="Updated Name")

        updated = UserService.update_user_profile(
            db_session, user.id, update_data, user
        )

        assert updated.full_name == "Updated Name"

    def test_update_user_profile_admin(self, db_session):
        """Test admin updating another user's profile."""
        admin = User(
            username="admin",
            email="admin@company.com",
            full_name="Admin User",
            role=UserRole.ADMIN,
        )
        member = User(
            username="member",
            email="member@company.com",
            full_name="Member User",
            role=UserRole.MEMBER,
        )
        db_session.add_all([admin, member])
        db_session.commit()

        update_data = UserUpdate(full_name="Updated by Admin")

        updated = UserService.update_user_profile(
            db_session, member.id, update_data, admin
        )

        assert updated.full_name == "Updated by Admin"

    def test_get_user_stats(self, db_session):
        """Test getting user statistics."""
        from src.models.prompt import Prompt
        from src.constants import PlatformTag, PromptStatus

        user = User(
            username="testuser",
            email="testuser@company.com",
            full_name="Test User",
            role=UserRole.MEMBER,
        )
        db_session.add(user)
        db_session.commit()

        # Create a prompt for the user
        prompt = Prompt(
            title="Test Prompt",
            content="Content",
            platform_tags=[PlatformTag.GITHUB_COPILOT],
            author_id=user.id,
            status=PromptStatus.PUBLISHED,
            view_count=10,
        )
        db_session.add(prompt)
        db_session.commit()

        stats = UserService.get_user_stats(db_session, user.id)

        assert stats["prompt_count"] == 1
        assert stats["total_prompt_views"] == 10

