"""Tests for rating router endpoints."""

import pytest
from fastapi import status

from src.constants import PlatformTag, PromptStatus, UserRole
from src.models.prompt import Prompt
from src.models.user import User
from src.services.auth_service import AuthService


class TestRatingRouter:
    """Test cases for rating router."""

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

    def test_create_rating_success(self, client, db_session):
        """Test creating a rating successfully."""
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

        rating_data = {"rating": 5}

        response = client.post(
            f"/api/prompts/{prompt.id}/ratings",
            json=rating_data,
            headers=headers,
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["rating"] == 5

    def test_get_rating_summary(self, client, db_session):
        """Test getting rating summary."""
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

        response = client.get(f"/api/prompts/{prompt.id}/ratings/summary")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["prompt_id"] == str(prompt.id)
        assert data["average_rating"] == 0.0
        assert data["total_ratings"] == 0

