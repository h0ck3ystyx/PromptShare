"""Tests for onboarding router endpoints."""

import pytest
from fastapi import status
from sqlalchemy.orm import Session

from src.constants import PlatformTag, PromptStatus, UserRole
from src.models.collection import Collection
from src.models.faq import FAQ
from src.models.prompt import Prompt
from src.models.user import User


class TestOnboardingRouter:
    """Test cases for onboarding router."""

    def test_get_onboarding_materials(self, client, db_session: Session):
        """Test getting onboarding materials."""
        # Create some test data
        user = User(
            username="testuser",
            email="test@example.com",
            full_name="Test User",
            role=UserRole.MEMBER,
        )
        db_session.add(user)
        db_session.flush()  # Flush to get user.id

        # Create featured collection
        collection = Collection(
            name="Getting Started Collection",
            description="A collection for new users",
            created_by_id=user.id,
            is_featured=True,
            display_order=0,
        )
        db_session.add(collection)
        db_session.flush()

        # Create FAQ
        faq = FAQ(
            question="How do I get started?",
            answer="Follow the onboarding guide.",
            category="getting_started",
            is_active=True,
            created_by_id=user.id,
        )
        db_session.add(faq)
        db_session.commit()

        response = client.get("/api/onboarding")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "welcome_message" in data
        assert "getting_started" in data
        assert "featured_collections" in data
        assert "quick_tips" in data
        assert "faqs" in data
        assert len(data["getting_started"]) > 0
        assert len(data["quick_tips"]) > 0

    def test_get_best_practices(self, client, db_session: Session):
        """Test getting best practices."""
        response = client.get("/api/onboarding/best-practices")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "general_tips" in data
        assert "platform_specific_tips" in data
        assert "common_mistakes" in data
        assert "resources" in data
        assert len(data["general_tips"]) > 0
        assert "github_copilot" in data["platform_specific_tips"]
        assert "o365_copilot" in data["platform_specific_tips"]
        assert "cursor" in data["platform_specific_tips"]
        assert "claude" in data["platform_specific_tips"]

    def test_onboarding_endpoints_public(self, client):
        """Test that onboarding endpoints are publicly accessible."""
        # Should not require authentication
        response = client.get("/api/onboarding")
        assert response.status_code == status.HTTP_200_OK

        response = client.get("/api/onboarding/best-practices")
        assert response.status_code == status.HTTP_200_OK

