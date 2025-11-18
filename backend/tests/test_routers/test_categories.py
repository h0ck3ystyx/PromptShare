"""Tests for category router endpoints."""

import pytest
from fastapi import status
from uuid import uuid4

from src.constants import UserRole
from src.models.category import Category
from src.models.user import User
from src.services.auth_service import AuthService


class TestCategoryRouter:
    """Test cases for category router."""

    def get_auth_headers(self, client, db_session, user_role=UserRole.MEMBER):
        """Helper to get auth headers for a user."""
        # Create user
        user = User(
            username=f"testuser_{user_role.value}",
            email=f"testuser_{user_role.value}@company.com",
            full_name=f"Test User {user_role.value}",
            role=user_role,
        )
        db_session.add(user)
        db_session.commit()

        # Create token
        token = AuthService.create_access_token(user.id)
        return {"Authorization": f"Bearer {token}"}, user

    def test_list_categories_empty(self, client, db_session):
        """Test listing categories when none exist."""
        response = client.get("/api/categories")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total"] == 0
        assert len(data["items"]) == 0

    def test_list_categories_with_data(self, client, db_session):
        """Test listing categories with data."""
        # Create categories
        cat1 = Category(name="Category 1", slug="category-1", description="First category")
        cat2 = Category(name="Category 2", slug="category-2", description="Second category")
        db_session.add_all([cat1, cat2])
        db_session.commit()

        response = client.get("/api/categories")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total"] == 2
        assert len(data["items"]) == 2

    def test_get_category_by_id(self, client, db_session):
        """Test getting category by ID."""
        category = Category(name="Test Category", slug="test-category", description="Test")
        db_session.add(category)
        db_session.commit()

        response = client.get(f"/api/categories/{category.id}")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == str(category.id)
        assert data["name"] == "Test Category"
        assert data["slug"] == "test-category"

    def test_get_category_by_id_not_found(self, client, db_session):
        """Test getting non-existent category by ID."""
        fake_id = uuid4()
        response = client.get(f"/api/categories/{fake_id}")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_category_by_slug(self, client, db_session):
        """Test getting category by slug."""
        category = Category(name="Test Category", slug="test-category", description="Test")
        db_session.add(category)
        db_session.commit()

        response = client.get("/api/categories/slug/test-category")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["slug"] == "test-category"
        assert data["name"] == "Test Category"

    def test_get_category_by_slug_not_found(self, client, db_session):
        """Test getting non-existent category by slug."""
        response = client.get("/api/categories/slug/non-existent")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_create_category_as_admin(self, client, db_session):
        """Test creating category as admin."""
        headers, user = self.get_auth_headers(client, db_session, UserRole.ADMIN)

        response = client.post(
            "/api/categories",
            json={
                "name": "New Category",
                "slug": "new-category",
                "description": "A new category",
            },
            headers=headers,
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["name"] == "New Category"
        assert data["slug"] == "new-category"

    def test_create_category_as_moderator(self, client, db_session):
        """Test creating category as moderator."""
        headers, user = self.get_auth_headers(client, db_session, UserRole.MODERATOR)

        response = client.post(
            "/api/categories",
            json={
                "name": "Mod Category",
                "slug": "mod-category",
                "description": "Moderator category",
            },
            headers=headers,
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["name"] == "Mod Category"

    def test_create_category_as_member_forbidden(self, client, db_session):
        """Test that members cannot create categories."""
        headers, user = self.get_auth_headers(client, db_session, UserRole.MEMBER)

        response = client.post(
            "/api/categories",
            json={
                "name": "Member Category",
                "slug": "member-category",
                "description": "Should fail",
            },
            headers=headers,
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_create_category_duplicate_slug(self, client, db_session):
        """Test creating category with duplicate slug."""
        # Create existing category
        existing = Category(name="Existing", slug="existing", description="Exists")
        db_session.add(existing)
        db_session.commit()

        headers, user = self.get_auth_headers(client, db_session, UserRole.ADMIN)

        response = client.post(
            "/api/categories",
            json={
                "name": "New Name",
                "slug": "existing",  # Duplicate slug
                "description": "Should fail",
            },
            headers=headers,
        )

        assert response.status_code == status.HTTP_409_CONFLICT

    def test_update_category_as_admin(self, client, db_session):
        """Test updating category as admin."""
        category = Category(name="Original", slug="original", description="Original desc")
        db_session.add(category)
        db_session.commit()

        headers, user = self.get_auth_headers(client, db_session, UserRole.ADMIN)

        response = client.put(
            f"/api/categories/{category.id}",
            json={
                "name": "Updated",
                "description": "Updated description",
            },
            headers=headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["name"] == "Updated"
        assert data["description"] == "Updated description"

    def test_update_category_as_member_forbidden(self, client, db_session):
        """Test that members cannot update categories."""
        category = Category(name="Test", slug="test", description="Test")
        db_session.add(category)
        db_session.commit()

        headers, user = self.get_auth_headers(client, db_session, UserRole.MEMBER)

        response = client.put(
            f"/api/categories/{category.id}",
            json={"name": "Updated"},
            headers=headers,
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_delete_category_as_admin(self, client, db_session):
        """Test deleting category as admin."""
        category = Category(name="To Delete", slug="to-delete", description="Delete me")
        db_session.add(category)
        db_session.commit()
        category_id = category.id

        headers, user = self.get_auth_headers(client, db_session, UserRole.ADMIN)

        response = client.delete(f"/api/categories/{category_id}", headers=headers)

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["message"] == "Category deleted successfully"

        # Verify deleted
        get_response = client.get(f"/api/categories/{category_id}")
        assert get_response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_category_as_moderator_forbidden(self, client, db_session):
        """Test that moderators cannot delete categories."""
        category = Category(name="Test", slug="test", description="Test")
        db_session.add(category)
        db_session.commit()

        headers, user = self.get_auth_headers(client, db_session, UserRole.MODERATOR)

        response = client.delete(f"/api/categories/{category.id}", headers=headers)

        assert response.status_code == status.HTTP_403_FORBIDDEN

