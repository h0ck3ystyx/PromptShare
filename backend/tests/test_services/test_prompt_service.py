"""Tests for prompt service."""

import pytest
from fastapi import HTTPException, status
from uuid import uuid4

from src.constants import PlatformTag, PromptStatus, UserRole
from src.models.category import Category
from src.models.prompt import Prompt
from src.models.user import User
from src.schemas.prompt import PromptCreate, PromptUpdate
from src.services.prompt_service import PromptService


class TestPromptService:
    """Test cases for PromptService."""

    def test_create_prompt_success(self, db_session):
        """Test creating a prompt successfully."""
        # Create author user
        author = User(
            username="testauthor",
            email="testauthor@company.com",
            full_name="Test Author",
            role=UserRole.MEMBER,
        )
        db_session.add(author)
        db_session.commit()

        # Create prompt data
        prompt_data = PromptCreate(
            title="Test Prompt",
            description="A test prompt",
            content="This is the prompt content",
            platform_tags=[PlatformTag.GITHUB_COPILOT],
            use_cases=["Code generation"],
            usage_tips="Use this for generating code",
            status=PromptStatus.DRAFT,
        )

        prompt = PromptService.create_prompt(
            db=db_session,
            prompt_data=prompt_data,
            author_id=author.id,
        )

        assert prompt.id is not None
        assert prompt.title == "Test Prompt"
        assert prompt.content == "This is the prompt content"
        assert prompt.author_id == author.id
        assert prompt.status == PromptStatus.DRAFT
        assert prompt.view_count == 0

    def test_create_prompt_with_categories(self, db_session):
        """Test creating a prompt with categories."""
        # Create author user
        author = User(
            username="testauthor",
            email="testauthor@company.com",
            full_name="Test Author",
            role=UserRole.MEMBER,
        )
        db_session.add(author)

        # Create categories
        category1 = Category(name="Python", slug="python", description="Python prompts")
        category2 = Category(name="JavaScript", slug="javascript", description="JS prompts")
        db_session.add_all([category1, category2])
        db_session.commit()

        # Create prompt with categories
        prompt_data = PromptCreate(
            title="Test Prompt",
            content="Prompt content",
            platform_tags=[PlatformTag.GITHUB_COPILOT],
            category_ids=[category1.id, category2.id],
        )

        prompt = PromptService.create_prompt(
            db=db_session,
            prompt_data=prompt_data,
            author_id=author.id,
        )

        assert len(prompt.categories) == 2
        assert category1 in prompt.categories
        assert category2 in prompt.categories

    def test_create_prompt_invalid_category(self, db_session):
        """Test creating a prompt with invalid category IDs."""
        # Create author user
        author = User(
            username="testauthor",
            email="testauthor@company.com",
            full_name="Test Author",
            role=UserRole.MEMBER,
        )
        db_session.add(author)
        db_session.commit()

        # Create prompt with non-existent category
        prompt_data = PromptCreate(
            title="Test Prompt",
            content="Prompt content",
            platform_tags=[PlatformTag.GITHUB_COPILOT],
            category_ids=[uuid4()],  # Non-existent category
        )

        with pytest.raises(HTTPException) as exc_info:
            PromptService.create_prompt(
                db=db_session,
                prompt_data=prompt_data,
                author_id=author.id,
            )

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert "not found" in exc_info.value.detail.lower()

    def test_get_prompt_by_id(self, db_session):
        """Test getting a prompt by ID."""
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

        # Get prompt
        retrieved = PromptService.get_prompt_by_id(db_session, prompt.id)

        assert retrieved is not None
        assert retrieved.id == prompt.id
        assert retrieved.title == "Test Prompt"

    def test_get_prompt_by_id_increment_view(self, db_session):
        """Test getting a prompt with view count increment."""
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
            view_count=5,
        )
        db_session.add(prompt)
        db_session.commit()

        # Get prompt with increment
        retrieved = PromptService.get_prompt_by_id(
            db_session, prompt.id, increment_view=True
        )

        assert retrieved.view_count == 6

    def test_get_prompts_with_filters(self, db_session):
        """Test getting prompts with various filters."""
        # Create users
        author1 = User(
            username="author1",
            email="author1@company.com",
            full_name="Author 1",
            role=UserRole.MEMBER,
        )
        author2 = User(
            username="author2",
            email="author2@company.com",
            full_name="Author 2",
            role=UserRole.MEMBER,
        )
        db_session.add_all([author1, author2])

        # Create prompts
        prompt1 = Prompt(
            title="Prompt 1",
            content="Content 1",
            platform_tags=[PlatformTag.GITHUB_COPILOT],
            author_id=author1.id,
            status=PromptStatus.PUBLISHED,
            is_featured=True,
        )
        prompt2 = Prompt(
            title="Prompt 2",
            content="Content 2",
            platform_tags=[PlatformTag.CURSOR],
            author_id=author2.id,
            status=PromptStatus.PUBLISHED,
            is_featured=False,
        )
        prompt3 = Prompt(
            title="Prompt 3",
            content="Content 3",
            platform_tags=[PlatformTag.GITHUB_COPILOT],
            author_id=author1.id,
            status=PromptStatus.DRAFT,
        )
        db_session.add_all([prompt1, prompt2, prompt3])
        db_session.commit()

        # Test status filter
        prompts, total = PromptService.get_prompts(
            db_session, status_filter=PromptStatus.PUBLISHED
        )
        assert total == 2
        assert len(prompts) == 2

        # Test author filter
        prompts, total = PromptService.get_prompts(
            db_session, author_id=author1.id
        )
        assert total == 2  # prompt1 and prompt3 (draft not excluded by default)

        # Test featured filter
        prompts, total = PromptService.get_prompts(
            db_session, featured_only=True
        )
        assert total == 1
        assert prompts[0].id == prompt1.id

    def test_update_prompt_author(self, db_session):
        """Test updating a prompt by its author."""
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

        # Update prompt
        update_data = PromptUpdate(
            title="Updated Title",
            content="Updated content",
        )

        updated = PromptService.update_prompt(
            db_session, prompt.id, update_data, author
        )

        assert updated.title == "Updated Title"
        assert updated.content == "Updated content"

    def test_update_prompt_admin(self, db_session):
        """Test updating a prompt by admin."""
        # Create author and admin
        author = User(
            username="testauthor",
            email="testauthor@company.com",
            full_name="Test Author",
            role=UserRole.MEMBER,
        )
        admin = User(
            username="admin",
            email="admin@company.com",
            full_name="Admin User",
            role=UserRole.ADMIN,
        )
        db_session.add_all([author, admin])
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

        # Update prompt as admin
        update_data = PromptUpdate(title="Admin Updated Title")

        updated = PromptService.update_prompt(
            db_session, prompt.id, update_data, admin
        )

        assert updated.title == "Admin Updated Title"

    def test_update_prompt_unauthorized(self, db_session):
        """Test updating a prompt by unauthorized user."""
        # Create users
        author = User(
            username="testauthor",
            email="testauthor@company.com",
            full_name="Test Author",
            role=UserRole.MEMBER,
        )
        other_user = User(
            username="otheruser",
            email="otheruser@company.com",
            full_name="Other User",
            role=UserRole.MEMBER,
        )
        db_session.add_all([author, other_user])
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

        # Try to update as other user
        update_data = PromptUpdate(title="Unauthorized Update")

        with pytest.raises(HTTPException) as exc_info:
            PromptService.update_prompt(
                db_session, prompt.id, update_data, other_user
            )

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN

    def test_delete_prompt_author(self, db_session):
        """Test deleting a prompt by its author."""
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
        prompt_id = prompt.id

        # Delete prompt
        PromptService.delete_prompt(db_session, prompt_id, author)

        # Verify deleted
        deleted = db_session.query(Prompt).filter(Prompt.id == prompt_id).first()
        assert deleted is None

    def test_delete_prompt_unauthorized(self, db_session):
        """Test deleting a prompt by unauthorized user."""
        # Create users
        author = User(
            username="testauthor",
            email="testauthor@company.com",
            full_name="Test Author",
            role=UserRole.MEMBER,
        )
        other_user = User(
            username="otheruser",
            email="otheruser@company.com",
            full_name="Other User",
            role=UserRole.MEMBER,
        )
        db_session.add_all([author, other_user])
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

        # Try to delete as other user
        with pytest.raises(HTTPException) as exc_info:
            PromptService.delete_prompt(db_session, prompt.id, other_user)

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN

    def test_track_copy(self, db_session):
        """Test tracking a prompt copy event."""
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
        )
        db_session.add(prompt)
        db_session.commit()

        # Track copy (should not raise exception)
        PromptService.track_copy(db_session, prompt.id)

        # Verify prompt still exists
        retrieved = db_session.query(Prompt).filter(Prompt.id == prompt.id).first()
        assert retrieved is not None

    def test_track_copy_nonexistent_prompt(self, db_session):
        """Test tracking copy for non-existent prompt."""
        with pytest.raises(HTTPException) as exc_info:
            PromptService.track_copy(db_session, uuid4())

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND

