"""Tests for prompt router endpoints."""

import pytest
from fastapi import status
from uuid import uuid4

from src.constants import PlatformTag, PromptStatus, UserRole
from src.models.category import Category
from src.models.prompt import Prompt
from src.models.user import User
from src.services.auth_service import AuthService


class TestPromptRouter:
    """Test cases for prompt router."""

    def get_auth_headers(self, client, db_session, username="testuser"):
        """Helper to get auth headers for a user."""
        # Create user
        user = User(
            username=username,
            email=f"{username}@company.com",
            full_name=f"{username.title()} User",
            role=UserRole.MEMBER,
        )
        db_session.add(user)
        db_session.commit()

        # Create token
        token = AuthService.create_access_token(user.id)
        return {"Authorization": f"Bearer {token}"}

    def test_list_prompts_empty(self, client, db_session):
        """Test listing prompts when none exist."""
        response = client.get("/api/prompts")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total"] == 0
        assert len(data["items"]) == 0

    def test_list_prompts_with_data(self, client, db_session):
        """Test listing prompts with data."""
        # Create author
        author = User(
            username="testauthor",
            email="testauthor@company.com",
            full_name="Test Author",
            role=UserRole.MEMBER,
        )
        db_session.add(author)
        db_session.commit()

        # Create prompts
        prompt1 = Prompt(
            title="Prompt 1",
            content="Content 1",
            platform_tags=[PlatformTag.GITHUB_COPILOT],
            author_id=author.id,
            status=PromptStatus.PUBLISHED,
        )
        prompt2 = Prompt(
            title="Prompt 2",
            content="Content 2",
            platform_tags=[PlatformTag.CURSOR],
            author_id=author.id,
            status=PromptStatus.PUBLISHED,
        )
        db_session.add_all([prompt1, prompt2])
        db_session.commit()

        response = client.get("/api/prompts")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total"] == 2
        assert len(data["items"]) == 2

    def test_list_prompts_with_filters(self, client, db_session):
        """Test listing prompts with filters."""
        # Create author
        author = User(
            username="testauthor",
            email="testauthor@company.com",
            full_name="Test Author",
            role=UserRole.MEMBER,
        )
        db_session.add(author)
        db_session.commit()

        # Create prompts
        prompt1 = Prompt(
            title="GitHub Prompt",
            content="Content 1",
            platform_tags=[PlatformTag.GITHUB_COPILOT],
            author_id=author.id,
            status=PromptStatus.PUBLISHED,
        )
        prompt2 = Prompt(
            title="Cursor Prompt",
            content="Content 2",
            platform_tags=[PlatformTag.CURSOR],
            author_id=author.id,
            status=PromptStatus.PUBLISHED,
        )
        db_session.add_all([prompt1, prompt2])
        db_session.commit()

        # Filter by platform
        response = client.get(
            "/api/prompts",
            params={"platform_tag": PlatformTag.GITHUB_COPILOT},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["title"] == "GitHub Prompt"

    def test_get_prompt_by_id(self, client, db_session):
        """Test getting a prompt by ID."""
        # Create author
        author = User(
            username="testauthor",
            email="testauthor@company.com",
            full_name="Test Author",
            role=UserRole.MEMBER,
        )
        db_session.add(author)
        db_session.commit()

        # Create prompt
        prompt = Prompt(
            title="Test Prompt",
            content="Prompt content",
            platform_tags=[PlatformTag.GITHUB_COPILOT],
            author_id=author.id,
            status=PromptStatus.PUBLISHED,
        )
        db_session.add(prompt)
        db_session.commit()

        response = client.get(f"/api/prompts/{prompt.id}")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == str(prompt.id)
        assert data["title"] == "Test Prompt"
        assert data["author_username"] == "testauthor"

    def test_get_prompt_not_found(self, client, db_session):
        """Test getting a non-existent prompt."""
        response = client.get(f"/api/prompts/{uuid4()}")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_create_prompt_success(self, client, db_session):
        """Test creating a prompt successfully."""
        headers = self.get_auth_headers(client, db_session)

        prompt_data = {
            "title": "New Prompt",
            "description": "A new prompt",
            "content": "This is the prompt content",
            "platform_tags": [PlatformTag.GITHUB_COPILOT.value],
            "use_cases": ["Code generation"],
            "usage_tips": "Use this for generating code",
            "status": PromptStatus.DRAFT.value,
        }

        response = client.post("/api/prompts", json=prompt_data, headers=headers)

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["title"] == "New Prompt"
        assert data["content"] == "This is the prompt content"
        assert data["status"] == PromptStatus.DRAFT.value

    def test_create_prompt_with_categories(self, client, db_session):
        """Test creating a prompt with categories."""
        headers = self.get_auth_headers(client, db_session)

        # Create categories
        category1 = Category(name="Python", slug="python", description="Python prompts")
        category2 = Category(name="JavaScript", slug="javascript", description="JS prompts")
        db_session.add_all([category1, category2])
        db_session.commit()

        prompt_data = {
            "title": "New Prompt",
            "content": "Prompt content",
            "platform_tags": [PlatformTag.GITHUB_COPILOT.value],
            "category_ids": [str(category1.id), str(category2.id)],
        }

        response = client.post("/api/prompts", json=prompt_data, headers=headers)

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert len(data["category_ids"]) == 2

    def test_create_prompt_unauthorized(self, client, db_session):
        """Test creating a prompt without authentication."""
        prompt_data = {
            "title": "New Prompt",
            "content": "Prompt content",
            "platform_tags": [PlatformTag.GITHUB_COPILOT.value],
        }

        response = client.post("/api/prompts", json=prompt_data)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_update_prompt_author(self, client, db_session):
        """Test updating a prompt by its author."""
        # Create author and get auth headers
        author = User(
            username="testauthor",
            email="testauthor@company.com",
            full_name="Test Author",
            role=UserRole.MEMBER,
        )
        db_session.add(author)
        db_session.commit()
        token = AuthService.create_access_token(author.id)
        headers = {"Authorization": f"Bearer {token}"}

        # Create prompt
        prompt = Prompt(
            title="Original Title",
            content="Original content",
            platform_tags=[PlatformTag.GITHUB_COPILOT],
            author_id=author.id,
        )
        db_session.add(prompt)
        db_session.commit()

        # Update prompt
        update_data = {
            "title": "Updated Title",
            "content": "Updated content",
        }

        response = client.put(
            f"/api/prompts/{prompt.id}",
            json=update_data,
            headers=headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["title"] == "Updated Title"
        assert data["content"] == "Updated content"

    def test_update_prompt_unauthorized(self, client, db_session):
        """Test updating a prompt by unauthorized user."""
        # Create author
        author = User(
            username="testauthor",
            email="testauthor@company.com",
            full_name="Test Author",
            role=UserRole.MEMBER,
        )
        db_session.add(author)
        db_session.commit()

        # Create prompt
        prompt = Prompt(
            title="Original Title",
            content="Original content",
            platform_tags=[PlatformTag.GITHUB_COPILOT],
            author_id=author.id,
        )
        db_session.add(prompt)
        db_session.commit()

        # Get auth headers for different user
        headers = self.get_auth_headers(client, db_session, username="otheruser")

        # Try to update
        update_data = {"title": "Unauthorized Update"}

        response = client.put(
            f"/api/prompts/{prompt.id}",
            json=update_data,
            headers=headers,
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_delete_prompt_author(self, client, db_session):
        """Test deleting a prompt by its author."""
        # Create author and get auth headers
        author = User(
            username="testauthor",
            email="testauthor@company.com",
            full_name="Test Author",
            role=UserRole.MEMBER,
        )
        db_session.add(author)
        db_session.commit()
        token = AuthService.create_access_token(author.id)
        headers = {"Authorization": f"Bearer {token}"}

        # Create prompt
        prompt = Prompt(
            title="Test Prompt",
            content="Prompt content",
            platform_tags=[PlatformTag.GITHUB_COPILOT],
            author_id=author.id,
        )
        db_session.add(prompt)
        db_session.commit()
        prompt_id = prompt.id

        # Delete prompt
        response = client.delete(f"/api/prompts/{prompt_id}", headers=headers)

        assert response.status_code == status.HTTP_200_OK
        assert "deleted successfully" in response.json()["message"].lower()

        # Verify deleted
        get_response = client.get(f"/api/prompts/{prompt_id}")
        assert get_response.status_code == status.HTTP_404_NOT_FOUND

    def test_track_prompt_copy(self, client, db_session):
        """Test tracking a prompt copy event."""
        # Create author
        author = User(
            username="testauthor",
            email="testauthor@company.com",
            full_name="Test Author",
            role=UserRole.MEMBER,
        )
        db_session.add(author)
        db_session.commit()

        # Create prompt
        prompt = Prompt(
            title="Test Prompt",
            content="Prompt content",
            platform_tags=[PlatformTag.GITHUB_COPILOT],
            author_id=author.id,
        )
        db_session.add(prompt)
        db_session.commit()

        # Track copy
        response = client.post(f"/api/prompts/{prompt.id}/copy")

        assert response.status_code == status.HTTP_200_OK
        assert "tracked successfully" in response.json()["message"].lower()

    def test_track_prompt_copy_not_found(self, client, db_session):
        """Test tracking copy for non-existent prompt."""
        response = client.post(f"/api/prompts/{uuid4()}/copy")

        assert response.status_code == status.HTTP_404_NOT_FOUND

