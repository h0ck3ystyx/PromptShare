"""Tests for upvote router endpoints."""

import pytest
from fastapi import status

from src.constants import PlatformTag, PromptStatus, UserRole
from src.models.prompt import Prompt
from src.models.user import User
from src.services.auth_service import AuthService


class TestUpvoteRouter:
    """Test cases for upvote router."""

    def get_auth_headers(self, client, db_session, username="testuser"):
        """Helper to get auth headers for a user."""
        user = User(
            username=username,
            email=f"{username}@company.com",
            full_name=f"{username.title()} User",
            role=UserRole.MEMBER,
        )
        db_session.add(user)
        db_session.commit()

        token = AuthService.create_access_token(user.id)
        return {"Authorization": f"Bearer {token}"}

    def test_toggle_upvote_add(self, client, db_session):
        """Test adding an upvote."""
        headers = self.get_auth_headers(client, db_session)

        # Create author and prompt
        author = User(
            username="testauthor",
            email="testauthor@company.com",
            full_name="Test Author",
            role=UserRole.MEMBER,
        )
        db_session.add(author)
        db_session.commit()

        prompt = Prompt(
            title="Test Prompt",
            content="Prompt content",
            platform_tags=[PlatformTag.GITHUB_COPILOT],
            author_id=author.id,
            status=PromptStatus.PUBLISHED,
        )
        db_session.add(prompt)
        db_session.commit()

        response = client.post(
            f"/api/prompts/{prompt.id}/upvotes",
            headers=headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "id" in data
        assert data["prompt_id"] == str(prompt.id)

    def test_get_upvote_summary_anonymous(self, client, db_session):
        """Test getting upvote summary without authentication."""
        # Create author and prompt
        author = User(
            username="testauthor",
            email="testauthor@company.com",
            full_name="Test Author",
            role=UserRole.MEMBER,
        )
        db_session.add(author)
        db_session.commit()

        prompt = Prompt(
            title="Test Prompt",
            content="Prompt content",
            platform_tags=[PlatformTag.GITHUB_COPILOT],
            author_id=author.id,
            status=PromptStatus.PUBLISHED,
        )
        db_session.add(prompt)
        db_session.commit()

        response = client.get(f"/api/prompts/{prompt.id}/upvotes/summary")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["prompt_id"] == str(prompt.id)
        assert data["total_upvotes"] == 0
        assert data["user_has_upvoted"] is False

    def test_get_upvote_summary_authenticated(self, client, db_session):
        """Test getting upvote summary with authentication."""
        headers = self.get_auth_headers(client, db_session)

        # Create author and prompt
        author = User(
            username="testauthor",
            email="testauthor@company.com",
            full_name="Test Author",
            role=UserRole.MEMBER,
        )
        db_session.add(author)
        db_session.commit()

        prompt = Prompt(
            title="Test Prompt",
            content="Prompt content",
            platform_tags=[PlatformTag.GITHUB_COPILOT],
            author_id=author.id,
            status=PromptStatus.PUBLISHED,
        )
        db_session.add(prompt)
        db_session.commit()

        response = client.get(
            f"/api/prompts/{prompt.id}/upvotes/summary",
            headers=headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["prompt_id"] == str(prompt.id)
        assert "user_has_upvoted" in data

