"""Tests for collections router endpoints."""

from uuid import uuid4

import pytest
from fastapi import status
from sqlalchemy.orm import Session

from src.constants import PlatformTag, PromptStatus, UserRole
from src.models.collection import Collection
from src.models.prompt import Prompt
from src.models.user import User
from src.services.auth_service import AuthService


class TestCollectionsRouter:
    """Test cases for collections router."""

    def get_auth_headers(self, db_session: Session, user_role: UserRole = UserRole.MEMBER):
        """Helper to get auth headers for a user."""
        username = f"testuser_{uuid4().hex[:8]}"
        email = f"{username}@example.com"
        user = User(
            username=username,
            email=email,
            full_name=f"{username.title()} User",
            role=user_role,
        )
        db_session.add(user)
        db_session.commit()
        token = AuthService.create_access_token(user.id)
        return {"Authorization": f"Bearer {token}"}, user.id

    def test_create_collection_success(self, client, db_session: Session):
        """Test creating a collection successfully as admin."""
        headers, user_id = self.get_auth_headers(db_session, UserRole.ADMIN)

        # Create a published prompt
        prompt = Prompt(
            title="Test Prompt",
            content="Test content",
            platform_tags=[PlatformTag.GITHUB_COPILOT],
            author_id=user_id,
            status=PromptStatus.PUBLISHED,
        )
        db_session.add(prompt)
        db_session.commit()

        collection_data = {
            "name": "Test Collection",
            "description": "A test collection",
            "is_featured": False,
            "display_order": 0,
            "prompt_ids": [str(prompt.id)],
        }

        response = client.post("/api/collections", json=collection_data, headers=headers)

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["name"] == "Test Collection"
        assert data["description"] == "A test collection"
        assert len(data["prompts"]) == 1
        assert data["prompts"][0]["id"] == str(prompt.id)

    def test_create_collection_as_member_fails(self, client, db_session: Session):
        """Test that members cannot create collections (admin/moderator only)."""
        headers, user_id = self.get_auth_headers(db_session, UserRole.MEMBER)

        collection_data = {
            "name": "Test Collection",
            "description": "A test collection",
            "is_featured": False,
            "display_order": 0,
            "prompt_ids": [],
        }

        response = client.post("/api/collections", json=collection_data, headers=headers)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_create_featured_collection_as_admin_succeeds(self, client, db_session: Session):
        """Test that admins can create featured collections."""
        headers, user_id = self.get_auth_headers(db_session, UserRole.ADMIN)

        collection_data = {
            "name": "Featured Collection",
            "description": "A featured collection",
            "is_featured": True,
            "display_order": 0,
            "prompt_ids": [],
        }

        response = client.post("/api/collections", json=collection_data, headers=headers)

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["is_featured"] is True

    def test_list_collections(self, client, db_session: Session):
        """Test listing collections."""
        headers, user_id = self.get_auth_headers(db_session, UserRole.MEMBER)

        # Create a collection
        collection = Collection(
            name="Test Collection",
            description="A test collection",
            created_by_id=user_id,
            is_featured=False,
        )
        db_session.add(collection)
        db_session.commit()

        response = client.get("/api/collections")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total"] >= 1
        assert any(c["name"] == "Test Collection" for c in data["collections"])

    def test_list_featured_collections(self, client, db_session: Session):
        """Test listing only featured collections."""
        headers, user_id = self.get_auth_headers(db_session, UserRole.ADMIN)

        # Create featured and non-featured collections
        featured = Collection(
            name="Featured Collection",
            created_by_id=user_id,
            is_featured=True,
        )
        non_featured = Collection(
            name="Regular Collection",
            created_by_id=user_id,
            is_featured=False,
        )
        db_session.add_all([featured, non_featured])
        db_session.commit()

        response = client.get("/api/collections?featured_only=true")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert all(c["is_featured"] is True for c in data["collections"])

    def test_get_collection_by_id(self, client, db_session: Session):
        """Test getting a collection by ID."""
        headers, user_id = self.get_auth_headers(db_session, UserRole.MEMBER)

        collection = Collection(
            name="Test Collection",
            description="A test collection",
            created_by_id=user_id,
        )
        db_session.add(collection)
        db_session.commit()

        response = client.get(f"/api/collections/{collection.id}")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == str(collection.id)
        assert data["name"] == "Test Collection"

    def test_get_collection_not_found(self, client):
        """Test getting a non-existent collection."""
        response = client.get(f"/api/collections/{uuid4()}")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_collection_as_admin(self, client, db_session: Session):
        """Test updating a collection as admin."""
        headers, user_id = self.get_auth_headers(db_session, UserRole.ADMIN)

        # Create collection as admin
        collection = Collection(
            name="Original Name",
            created_by_id=user_id,
        )
        db_session.add(collection)
        db_session.commit()

        update_data = {"name": "Updated Name"}

        response = client.put(
            f"/api/collections/{collection.id}",
            json=update_data,
            headers=headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["name"] == "Updated Name"

    def test_delete_collection_as_admin(self, client, db_session: Session):
        """Test deleting a collection as admin."""
        headers, user_id = self.get_auth_headers(db_session, UserRole.ADMIN)

        # Create collection as admin
        collection = Collection(
            name="To Delete",
            created_by_id=user_id,
        )
        db_session.add(collection)
        db_session.commit()

        response = client.delete(f"/api/collections/{collection.id}", headers=headers)

        assert response.status_code == status.HTTP_200_OK

        # Verify collection is deleted
        response = client.get(f"/api/collections/{collection.id}")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_create_collection_requires_auth(self, client):
        """Test that creating a collection requires authentication."""
        collection_data = {
            "name": "Test Collection",
            "description": "A test collection",
            "prompt_ids": [],
        }

        response = client.post("/api/collections", json=collection_data)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

