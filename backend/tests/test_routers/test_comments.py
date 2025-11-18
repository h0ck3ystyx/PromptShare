"""Tests for comment router endpoints."""

import pytest
from fastapi import status

from src.constants import PlatformTag, PromptStatus, UserRole
from src.models.comment import Comment
from src.models.prompt import Prompt
from src.models.user import User
from src.services.auth_service import AuthService


class TestCommentRouter:
    """Test cases for comment router."""

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

    def test_get_comments_empty(self, client, db_session):
        """Test getting comments when none exist."""
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

        response = client.get(f"/api/prompts/{prompt.id}/comments")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 0

    def test_create_comment_success(self, client, db_session):
        """Test creating a comment successfully."""
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

        comment_data = {"content": "This is a great prompt!"}

        response = client.post(
            f"/api/prompts/{prompt.id}/comments",
            json=comment_data,
            headers=headers,
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["content"] == "This is a great prompt!"

    def test_create_comment_unauthorized(self, client, db_session):
        """Test creating a comment without authentication."""
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

        comment_data = {"content": "Comment"}

        response = client.post(
            f"/api/prompts/{prompt.id}/comments",
            json=comment_data,
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_comments_with_deleted_permission(self, client, db_session):
        """Test that non-admins cannot view deleted comments."""
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

        # Create deleted comment
        comment = Comment(
            prompt_id=prompt.id,
            user_id=author.id,
            content="Deleted comment",
            is_deleted=True,
        )
        db_session.add(comment)
        db_session.commit()

        # Try to get deleted comments as regular user
        headers = self.get_auth_headers(client, db_session)
        response = client.get(
            f"/api/prompts/{prompt.id}/comments",
            params={"include_deleted": True},
            headers=headers,
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_comments_tree_mode(self, client, db_session):
        """Test getting comments in tree mode."""
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

        # Create parent and reply
        parent = Comment(
            prompt_id=prompt.id,
            user_id=author.id,
            content="Parent comment",
        )
        db_session.add(parent)
        db_session.commit()

        reply = Comment(
            prompt_id=prompt.id,
            user_id=author.id,
            content="Reply",
            parent_comment_id=parent.id,
        )
        db_session.add(reply)
        db_session.commit()

        response = client.get(
            f"/api/prompts/{prompt.id}/comments",
            params={"tree": True},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 1
        assert "replies" in data[0]

