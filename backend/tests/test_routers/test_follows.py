"""Tests for follow router endpoints."""

from uuid import uuid4

import pytest
from fastapi import status

from src.constants import UserRole
from src.models.category import Category
from src.models.user import User
from src.services.auth_service import AuthService


class TestFollowRouter:
    """Test cases for follow router."""

    def get_auth_headers(self, client, db_session, user_role=UserRole.MEMBER):
        """Helper to get auth headers for a user."""
        user = User(
            username=f"testuser_{user_role.value}",
            email=f"testuser_{user_role.value}@company.com",
            full_name=f"Test User {user_role.value}",
            role=user_role,
        )
        db_session.add(user)
        db_session.commit()

        token = AuthService.create_access_token(user.id)
        return {"Authorization": f"Bearer {token}"}, user

    def test_follow_category_success(self, client, db_session):
        """Test successfully following a category."""
        headers, user = self.get_auth_headers(client, db_session)

        category = Category(name="Test Category", slug="test-category", description="Test")
        db_session.add(category)
        db_session.commit()

        response = client.post(
            f"/api/follows/categories/{category.id}",
            headers=headers,
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["user_id"] == str(user.id)
        assert data["category_id"] == str(category.id)
        assert "category" in data

    def test_follow_category_not_found(self, client, db_session):
        """Test following a non-existent category."""
        headers, _ = self.get_auth_headers(client, db_session)

        response = client.post(
            f"/api/follows/categories/{uuid4()}",
            headers=headers,
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_follow_category_already_following(self, client, db_session):
        """Test following a category that is already being followed."""
        headers, user = self.get_auth_headers(client, db_session)

        category = Category(name="Test Category", slug="test-category", description="Test")
        db_session.add(category)
        db_session.commit()

        # Follow once
        response1 = client.post(
            f"/api/follows/categories/{category.id}",
            headers=headers,
        )
        assert response1.status_code == status.HTTP_201_CREATED

        # Try to follow again
        response2 = client.post(
            f"/api/follows/categories/{category.id}",
            headers=headers,
        )

        assert response2.status_code == status.HTTP_400_BAD_REQUEST

    def test_unfollow_category_success(self, client, db_session):
        """Test successfully unfollowing a category."""
        headers, user = self.get_auth_headers(client, db_session)

        category = Category(name="Test Category", slug="test-category", description="Test")
        db_session.add(category)
        db_session.commit()

        # Follow first
        response1 = client.post(
            f"/api/follows/categories/{category.id}",
            headers=headers,
        )
        assert response1.status_code == status.HTTP_201_CREATED

        # Unfollow
        response2 = client.delete(
            f"/api/follows/categories/{category.id}",
            headers=headers,
        )

        assert response2.status_code == status.HTTP_200_OK
        assert "successfully unfollowed" in response2.json()["message"].lower()

    def test_unfollow_category_not_following(self, client, db_session):
        """Test unfollowing a category that is not being followed."""
        headers, _ = self.get_auth_headers(client, db_session)

        category = Category(name="Test Category", slug="test-category", description="Test")
        db_session.add(category)
        db_session.commit()

        response = client.delete(
            f"/api/follows/categories/{category.id}",
            headers=headers,
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_my_follows(self, client, db_session):
        """Test getting categories followed by current user."""
        headers, user = self.get_auth_headers(client, db_session)

        # Create categories
        category1 = Category(name="Category 1", slug="category-1", description="Test")
        category2 = Category(name="Category 2", slug="category-2", description="Test")
        db_session.add_all([category1, category2])
        db_session.commit()

        # Follow categories
        client.post(f"/api/follows/categories/{category1.id}", headers=headers)
        client.post(f"/api/follows/categories/{category2.id}", headers=headers)

        # Get follows
        response = client.get("/api/follows/categories", headers=headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total"] == 2
        assert len(data["items"]) == 2

    def test_get_my_follows_pagination(self, client, db_session):
        """Test pagination for user follows."""
        headers, user = self.get_auth_headers(client, db_session)

        # Create multiple categories
        categories = []
        for i in range(5):
            cat = Category(name=f"Category {i}", slug=f"category-{i}", description="Test")
            categories.append(cat)
            db_session.add(cat)
        db_session.commit()

        # Follow all categories
        for cat in categories:
            client.post(f"/api/follows/categories/{cat.id}", headers=headers)

        # Get first page
        response1 = client.get("/api/follows/categories?page=1&page_size=2", headers=headers)
        assert response1.status_code == status.HTTP_200_OK
        data1 = response1.json()
        assert data1["total"] == 5
        assert len(data1["items"]) == 2

        # Get second page
        response2 = client.get("/api/follows/categories?page=2&page_size=2", headers=headers)
        assert response2.status_code == status.HTTP_200_OK
        data2 = response2.json()
        assert data2["total"] == 5
        assert len(data2["items"]) == 2

    def test_check_follow_status_following(self, client, db_session):
        """Test checking follow status when following."""
        headers, user = self.get_auth_headers(client, db_session)

        category = Category(name="Test Category", slug="test-category", description="Test")
        db_session.add(category)
        db_session.commit()

        # Follow category
        client.post(f"/api/follows/categories/{category.id}", headers=headers)

        # Check status
        response = client.get(
            f"/api/follows/categories/{category.id}/check",
            headers=headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["is_following"] is True

    def test_check_follow_status_not_following(self, client, db_session):
        """Test checking follow status when not following."""
        headers, user = self.get_auth_headers(client, db_session)

        category = Category(name="Test Category", slug="test-category", description="Test")
        db_session.add(category)
        db_session.commit()

        # Check status without following
        response = client.get(
            f"/api/follows/categories/{category.id}/check",
            headers=headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["is_following"] is False

    def test_follow_category_requires_auth(self, client, db_session):
        """Test that following requires authentication."""
        category = Category(name="Test Category", slug="test-category", description="Test")
        db_session.add(category)
        db_session.commit()

        response = client.post(f"/api/follows/categories/{category.id}")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_my_follows_requires_auth(self, client, db_session):
        """Test that getting follows requires authentication."""
        response = client.get("/api/follows/categories")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

