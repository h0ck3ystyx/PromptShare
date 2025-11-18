"""Tests for search service."""

from fastapi import status

from src.constants import PlatformTag, PromptStatus, SortOrder
from src.models.category import Category
from src.models.prompt import Prompt
from src.models.user import User
from src.services.search_service import SearchService


class TestSearchService:
    """Test cases for SearchService."""

    def test_search_prompts_by_keyword(self, db_session):
        """Test searching prompts by keyword."""
        # Create author
        author = User(
            username="author",
            email="author@company.com",
            full_name="Author User",
        )
        db_session.add(author)
        db_session.commit()

        # Create prompts
        prompt1 = Prompt(
            title="Python Development",
            description="Tips for Python development",
            content="Use type hints and docstrings",
            platform_tags=[PlatformTag.CURSOR],
            author_id=author.id,
            status=PromptStatus.PUBLISHED,
        )
        prompt2 = Prompt(
            title="JavaScript Tips",
            description="JavaScript best practices",
            content="Use const and let",
            platform_tags=[PlatformTag.GITHUB_COPILOT],
            author_id=author.id,
            status=PromptStatus.PUBLISHED,
        )
        db_session.add_all([prompt1, prompt2])
        db_session.commit()

        # Search for "Python"
        prompts, total = SearchService.search_prompts(
            db=db_session,
            query="Python",
            limit=10,
        )

        assert total == 1
        assert len(prompts) == 1
        assert prompts[0].title == "Python Development"

    def test_search_prompts_with_platform_filter(self, db_session):
        """Test searching prompts with platform filter."""
        author = User(
            username="author",
            email="author@company.com",
            full_name="Author User",
        )
        db_session.add(author)
        db_session.commit()

        prompt1 = Prompt(
            title="Cursor Prompt",
            content="Content for Cursor",
            platform_tags=[PlatformTag.CURSOR],
            author_id=author.id,
            status=PromptStatus.PUBLISHED,
        )
        prompt2 = Prompt(
            title="GitHub Prompt",
            content="Content for GitHub",
            platform_tags=[PlatformTag.GITHUB_COPILOT],
            author_id=author.id,
            status=PromptStatus.PUBLISHED,
        )
        db_session.add_all([prompt1, prompt2])
        db_session.commit()

        # Search with platform filter
        prompts, total = SearchService.search_prompts(
            db=db_session,
            query="Prompt",
            platform_tag=PlatformTag.CURSOR,
            limit=10,
        )

        assert total == 1
        assert prompts[0].title == "Cursor Prompt"

    def test_search_prompts_with_category_filter(self, db_session):
        """Test searching prompts with category filter."""
        author = User(
            username="author",
            email="author@company.com",
            full_name="Author User",
        )
        category1 = Category(name="Python", slug="python", description="Python category")
        category2 = Category(name="JavaScript", slug="javascript", description="JS category")
        db_session.add_all([author, category1, category2])
        db_session.commit()

        prompt1 = Prompt(
            title="Python Tips",
            content="Python content",
            platform_tags=[PlatformTag.CURSOR],
            author_id=author.id,
            status=PromptStatus.PUBLISHED,
        )
        prompt1.categories = [category1]

        prompt2 = Prompt(
            title="JS Tips",
            content="JavaScript content",
            platform_tags=[PlatformTag.CURSOR],
            author_id=author.id,
            status=PromptStatus.PUBLISHED,
        )
        prompt2.categories = [category2]

        db_session.add_all([prompt1, prompt2])
        db_session.commit()

        # Search with category filter
        prompts, total = SearchService.search_prompts(
            db=db_session,
            query="Tips",
            category_id=category1.id,
            limit=10,
        )

        assert total == 1
        assert prompts[0].title == "Python Tips"

    def test_search_prompts_sort_by_newest(self, db_session):
        """Test sorting prompts by newest."""
        from datetime import datetime, timedelta, timezone

        author = User(
            username="author",
            email="author@company.com",
            full_name="Author User",
        )
        db_session.add(author)
        db_session.commit()

        # Create prompts with different creation times
        prompt1 = Prompt(
            title="Old Prompt",
            content="Old content",
            platform_tags=[PlatformTag.CURSOR],
            author_id=author.id,
            status=PromptStatus.PUBLISHED,
            created_at=datetime.now(timezone.utc) - timedelta(days=2),
        )
        prompt2 = Prompt(
            title="New Prompt",
            content="New content",
            platform_tags=[PlatformTag.CURSOR],
            author_id=author.id,
            status=PromptStatus.PUBLISHED,
            created_at=datetime.now(timezone.utc),
        )
        db_session.add_all([prompt1, prompt2])
        db_session.commit()

        prompts, total = SearchService.search_prompts(
            db=db_session,
            sort_by=SortOrder.NEWEST,
            limit=10,
        )

        assert total == 2
        assert prompts[0].title == "New Prompt"
        assert prompts[1].title == "Old Prompt"

    def test_search_prompts_sort_by_most_viewed(self, db_session):
        """Test sorting prompts by most viewed."""
        author = User(
            username="author",
            email="author@company.com",
            full_name="Author User",
        )
        db_session.add(author)
        db_session.commit()

        prompt1 = Prompt(
            title="Low Views",
            content="Content 1",
            platform_tags=[PlatformTag.CURSOR],
            author_id=author.id,
            status=PromptStatus.PUBLISHED,
            view_count=10,
        )
        prompt2 = Prompt(
            title="High Views",
            content="Content 2",
            platform_tags=[PlatformTag.CURSOR],
            author_id=author.id,
            status=PromptStatus.PUBLISHED,
            view_count=100,
        )
        db_session.add_all([prompt1, prompt2])
        db_session.commit()

        prompts, total = SearchService.search_prompts(
            db=db_session,
            sort_by=SortOrder.MOST_VIEWED,
            limit=10,
        )

        assert total == 2
        assert prompts[0].title == "High Views"
        assert prompts[0].view_count == 100
        assert prompts[1].title == "Low Views"
        assert prompts[1].view_count == 10

    def test_search_prompts_featured_only(self, db_session):
        """Test searching only featured prompts."""
        author = User(
            username="author",
            email="author@company.com",
            full_name="Author User",
        )
        db_session.add(author)
        db_session.commit()

        prompt1 = Prompt(
            title="Featured Prompt",
            content="Featured content",
            platform_tags=[PlatformTag.CURSOR],
            author_id=author.id,
            status=PromptStatus.PUBLISHED,
            is_featured=True,
        )
        prompt2 = Prompt(
            title="Regular Prompt",
            content="Regular content",
            platform_tags=[PlatformTag.CURSOR],
            author_id=author.id,
            status=PromptStatus.PUBLISHED,
            is_featured=False,
        )
        db_session.add_all([prompt1, prompt2])
        db_session.commit()

        prompts, total = SearchService.search_prompts(
            db=db_session,
            featured_only=True,
            limit=10,
        )

        assert total == 1
        assert prompts[0].title == "Featured Prompt"

    def test_search_prompts_excludes_archived(self, db_session):
        """Test that archived prompts are excluded by default."""
        author = User(
            username="author",
            email="author@company.com",
            full_name="Author User",
        )
        db_session.add(author)
        db_session.commit()

        prompt1 = Prompt(
            title="Published Prompt",
            content="Published content",
            platform_tags=[PlatformTag.CURSOR],
            author_id=author.id,
            status=PromptStatus.PUBLISHED,
        )
        prompt2 = Prompt(
            title="Archived Prompt",
            content="Archived content",
            platform_tags=[PlatformTag.CURSOR],
            author_id=author.id,
            status=PromptStatus.ARCHIVED,
        )
        db_session.add_all([prompt1, prompt2])
        db_session.commit()

        prompts, total = SearchService.search_prompts(
            db=db_session,
            limit=10,
        )

        assert total == 1
        assert prompts[0].title == "Published Prompt"

    def test_search_prompts_pagination(self, db_session):
        """Test search pagination."""
        author = User(
            username="author",
            email="author@company.com",
            full_name="Author User",
        )
        db_session.add(author)
        db_session.commit()

        # Create multiple prompts
        prompts = []
        for i in range(5):
            prompt = Prompt(
                title=f"Prompt {i}",
                content=f"Content {i}",
                platform_tags=[PlatformTag.CURSOR],
                author_id=author.id,
                status=PromptStatus.PUBLISHED,
            )
            prompts.append(prompt)
        db_session.add_all(prompts)
        db_session.commit()

        # First page
        page1, total = SearchService.search_prompts(
            db=db_session,
            skip=0,
            limit=2,
        )

        assert total == 5
        assert len(page1) == 2

        # Second page
        page2, total = SearchService.search_prompts(
            db=db_session,
            skip=2,
            limit=2,
        )

        assert total == 5
        assert len(page2) == 2
        assert page1[0].id != page2[0].id

