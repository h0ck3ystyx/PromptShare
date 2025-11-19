"""Tests for FAQs router endpoints."""

from uuid import uuid4

import pytest
from fastapi import status
from sqlalchemy.orm import Session

from src.constants import UserRole
from src.models.faq import FAQ
from src.models.user import User
from src.services.auth_service import AuthService


class TestFAQsRouter:
    """Test cases for FAQs router."""

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

    def test_create_faq_success(self, client, db_session: Session):
        """Test creating an FAQ successfully."""
        headers, user_id = self.get_auth_headers(db_session, UserRole.MEMBER)

        faq_data = {
            "question": "What is PromptShare?",
            "answer": "PromptShare is a platform for sharing prompts.",
            "category": "getting_started",
            "display_order": 0,
            "is_active": True,
        }

        response = client.post("/api/faqs", json=faq_data, headers=headers)

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["question"] == "What is PromptShare?"
        assert data["answer"] == "PromptShare is a platform for sharing prompts."
        assert data["category"] == "getting_started"

    def test_list_faqs(self, client, db_session: Session):
        """Test listing FAQs."""
        headers, user_id = self.get_auth_headers(db_session, UserRole.MEMBER)

        # Create FAQs
        faq1 = FAQ(
            question="Question 1",
            answer="Answer 1",
            category="getting_started",
            is_active=True,
            created_by_id=user_id,
        )
        faq2 = FAQ(
            question="Question 2",
            answer="Answer 2",
            category="prompts",
            is_active=True,
            created_by_id=user_id,
        )
        db_session.add_all([faq1, faq2])
        db_session.commit()

        response = client.get("/api/faqs")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total"] >= 2

    def test_list_faqs_by_category(self, client, db_session: Session):
        """Test filtering FAQs by category."""
        headers, user_id = self.get_auth_headers(db_session, UserRole.MEMBER)

        faq1 = FAQ(
            question="Getting Started Question",
            answer="Answer",
            category="getting_started",
            is_active=True,
            created_by_id=user_id,
        )
        faq2 = FAQ(
            question="Prompts Question",
            answer="Answer",
            category="prompts",
            is_active=True,
            created_by_id=user_id,
        )
        db_session.add_all([faq1, faq2])
        db_session.commit()

        response = client.get("/api/faqs?category=getting_started")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert all(f["category"] == "getting_started" for f in data["faqs"])

    def test_list_faqs_active_only(self, client, db_session: Session):
        """Test filtering FAQs to show only active ones."""
        headers, user_id = self.get_auth_headers(db_session, UserRole.MEMBER)

        active_faq = FAQ(
            question="Active FAQ",
            answer="Answer",
            is_active=True,
            created_by_id=user_id,
        )
        inactive_faq = FAQ(
            question="Inactive FAQ",
            answer="Answer",
            is_active=False,
            created_by_id=user_id,
        )
        db_session.add_all([active_faq, inactive_faq])
        db_session.commit()

        response = client.get("/api/faqs?active_only=true")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert all(f["is_active"] is True for f in data["faqs"])

    def test_get_faq_by_id(self, client, db_session: Session):
        """Test getting an FAQ by ID."""
        headers, user_id = self.get_auth_headers(db_session, UserRole.MEMBER)

        faq = FAQ(
            question="Test Question",
            answer="Test Answer",
            created_by_id=user_id,
        )
        db_session.add(faq)
        db_session.commit()

        response = client.get(f"/api/faqs/{faq.id}")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == str(faq.id)
        assert data["question"] == "Test Question"

    def test_get_faq_not_found(self, client):
        """Test getting a non-existent FAQ."""
        response = client.get(f"/api/faqs/{uuid4()}")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_faq_as_creator(self, client, db_session: Session):
        """Test updating an FAQ as the creator."""
        headers, user_id = self.get_auth_headers(db_session, UserRole.MEMBER)

        faq = FAQ(
            question="Original Question",
            answer="Original Answer",
            created_by_id=user_id,
        )
        db_session.add(faq)
        db_session.commit()

        update_data = {"question": "Updated Question"}

        response = client.put(
            f"/api/faqs/{faq.id}",
            json=update_data,
            headers=headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["question"] == "Updated Question"

    def test_delete_faq_as_creator(self, client, db_session: Session):
        """Test deleting an FAQ as the creator."""
        headers, user_id = self.get_auth_headers(db_session, UserRole.MEMBER)

        faq = FAQ(
            question="To Delete",
            answer="Answer",
            created_by_id=user_id,
        )
        db_session.add(faq)
        db_session.commit()

        response = client.delete(f"/api/faqs/{faq.id}", headers=headers)

        assert response.status_code == status.HTTP_200_OK

        # Verify FAQ is deleted
        response = client.get(f"/api/faqs/{faq.id}")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_create_faq_requires_auth(self, client):
        """Test that creating an FAQ requires authentication."""
        faq_data = {
            "question": "Test Question",
            "answer": "Test Answer",
        }

        response = client.post("/api/faqs", json=faq_data)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

