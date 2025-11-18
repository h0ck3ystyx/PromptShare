"""Tests for search router endpoints."""

from fastapi import status

from src.constants import PlatformTag, PromptStatus, SortOrder
from src.models.category import Category
from src.models.prompt import Prompt
from src.models.user import User


class TestSearchRouter:
    """Test cases for search router."""

    def test_search_prompts_empty(self, client, db_session):
        """Test searching when no prompts exist."""
        response = client.get("/api/search")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total"] == 0
        assert len(data["items"]) == 0

    def test_search_prompts_by_query(self, client, db_session):
        """Test searching prompts by query string."""
        author = User(
            username="author",
            email="author@company.com",
            full_name="Author User",
        )
        db_session.add(author)
        db_session.commit()

        prompt = Prompt(
            title="Python Development Guide",
            description="A comprehensive guide",
            content="Learn Python programming",
            platform_tags=[PlatformTag.CURSOR],
            author_id=author.id,
            status=PromptStatus.PUBLISHED,
        )
        db_session.add(prompt)
        db_session.commit()

        response = client.get("/api/search", params={"q": "Python"})

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total"] == 1
        assert len(data["items"]) == 1
        assert "Python" in data["items"][0]["title"]

    def test_search_prompts_with_filters(self, client, db_session):
        """Test searching with platform and category filters."""
        author = User(
            username="author",
            email="author@company.com",
            full_name="Author User",
        )
        category = Category(name="Development", slug="development", description="Dev category")
        db_session.add_all([author, category])
        db_session.commit()

        prompt = Prompt(
            title="Cursor Tips",
            content="Tips for using Cursor",
            platform_tags=[PlatformTag.CURSOR],
            author_id=author.id,
            status=PromptStatus.PUBLISHED,
        )
        prompt.categories = [category]
        db_session.add(prompt)
        db_session.commit()

        response = client.get(
            "/api/search",
            params={
                "q": "Cursor",
                "platform": PlatformTag.CURSOR.value,
                "category": str(category.id),
            },
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total"] == 1

    def test_search_prompts_sort_by_most_viewed(self, client, db_session):
        """Test sorting search results by most viewed."""
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

        response = client.get(
            "/api/search",
            params={"sort_by": SortOrder.MOST_VIEWED.value},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total"] == 2
        assert data["items"][0]["title"] == "High Views"
        assert data["items"][0]["view_count"] == 100

    def test_search_prompts_pagination(self, client, db_session):
        """Test search pagination."""
        author = User(
            username="author",
            email="author@company.com",
            full_name="Author User",
        )
        db_session.add(author)
        db_session.commit()

        # Create multiple prompts
        for i in range(5):
            prompt = Prompt(
                title=f"Prompt {i}",
                content=f"Content {i}",
                platform_tags=[PlatformTag.CURSOR],
                author_id=author.id,
                status=PromptStatus.PUBLISHED,
            )
            db_session.add(prompt)
        db_session.commit()

        # First page
        response = client.get("/api/search", params={"page": 1, "page_size": 2})

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total"] == 5
        assert len(data["items"]) == 2
        assert data["page"] == 1
        assert data["page_size"] == 2
        assert data["total_pages"] == 3

        # Second page
        response = client.get("/api/search", params={"page": 2, "page_size": 2})

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["page"] == 2
        assert len(data["items"]) == 2

    def test_search_prompts_featured_only(self, client, db_session):
        """Test searching only featured prompts."""
        author = User(
            username="author",
            email="author@company.com",
            full_name="Author User",
        )
        db_session.add(author)
        db_session.commit()

        prompt1 = Prompt(
            title="Featured",
            content="Featured content",
            platform_tags=[PlatformTag.CURSOR],
            author_id=author.id,
            status=PromptStatus.PUBLISHED,
            is_featured=True,
        )
        prompt2 = Prompt(
            title="Regular",
            content="Regular content",
            platform_tags=[PlatformTag.CURSOR],
            author_id=author.id,
            status=PromptStatus.PUBLISHED,
            is_featured=False,
        )
        db_session.add_all([prompt1, prompt2])
        db_session.commit()

        response = client.get("/api/search", params={"featured": True})

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["title"] == "Featured"

