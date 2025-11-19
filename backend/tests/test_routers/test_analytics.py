"""Tests for analytics router endpoints."""

import pytest
from fastapi import status

from src.constants import AnalyticsEventType, PlatformTag, PromptStatus, UserRole
from src.models.analytics_event import AnalyticsEvent
from src.models.prompt import Prompt
from src.models.user import User
from src.services.auth_service import AuthService
from src.services.analytics_service import AnalyticsService


class TestAnalyticsRouter:
    """Test cases for analytics router."""

    def get_auth_headers(self, db_session, user: User):
        """Helper to get auth headers for a user."""
        token = AuthService.create_access_token(user.id)
        return {"Authorization": f"Bearer {token}"}

    def test_get_prompt_analytics_success(self, client, db_session):
        """Test getting analytics for a specific prompt (admin)."""
        # Create admin user
        admin = User(
            username="admin",
            email="admin@example.com",
            full_name="Admin User",
            role=UserRole.ADMIN,
        )
        author = User(
            username="author",
            email="author@example.com",
            full_name="Author User",
            role=UserRole.MEMBER,
        )
        prompt = Prompt(
            title="Test Prompt",
            content="Test content",
            platform_tags=[PlatformTag.GITHUB_COPILOT],
            author_id=author.id,
            status=PromptStatus.PUBLISHED,
        )
        db_session.add_all([admin, author, prompt])
        db_session.commit()

        # Create some events
        for _ in range(5):
            AnalyticsService.track_event(
                db=db_session,
                event_type=AnalyticsEventType.VIEW,
                prompt_id=prompt.id,
            )

        headers = self.get_auth_headers(db_session, admin)
        response = client.get(
            f"/api/analytics/prompts/{prompt.id}",
            headers=headers,
            params={"days": 30},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["prompt_id"] == str(prompt.id)
        assert data["prompt_title"] == prompt.title
        assert data["total_views"] == 5
        assert data["period_days"] == 30

    def test_get_prompt_analytics_not_found(self, client, db_session):
        """Test getting analytics for non-existent prompt."""
        from uuid import uuid4

        admin = User(
            username="admin",
            email="admin@example.com",
            full_name="Admin User",
            role=UserRole.ADMIN,
        )
        db_session.add(admin)
        db_session.commit()

        headers = self.get_auth_headers(db_session, admin)
        response = client.get(
            f"/api/analytics/prompts/{uuid4()}",
            headers=headers,
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_prompt_analytics_unauthorized(self, client, db_session):
        """Test getting analytics without admin access."""
        member = User(
            username="member",
            email="member@example.com",
            full_name="Member User",
            role=UserRole.MEMBER,
        )
        prompt = Prompt(
            title="Test Prompt",
            content="Test content",
            platform_tags=[PlatformTag.GITHUB_COPILOT],
            author_id=member.id,
            status=PromptStatus.PUBLISHED,
        )
        db_session.add_all([member, prompt])
        db_session.commit()

        headers = self.get_auth_headers(db_session, member)
        response = client.get(
            f"/api/analytics/prompts/{prompt.id}",
            headers=headers,
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_prompt_analytics_unauthenticated(self, client, db_session):
        """Test getting analytics without authentication."""
        from uuid import uuid4

        response = client.get(f"/api/analytics/prompts/{uuid4()}")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_overview_analytics_success(self, client, db_session):
        """Test getting overview analytics (admin)."""
        admin = User(
            username="admin",
            email="admin@example.com",
            full_name="Admin User",
            role=UserRole.ADMIN,
        )
        user = User(
            username="user",
            email="user@example.com",
            full_name="User",
            role=UserRole.MEMBER,
        )
        prompt = Prompt(
            title="Test Prompt",
            content="Test content",
            platform_tags=[PlatformTag.GITHUB_COPILOT],
            author_id=user.id,
            status=PromptStatus.PUBLISHED,
        )
        db_session.add_all([admin, user, prompt])
        db_session.commit()

        # Create some events
        for _ in range(10):
            AnalyticsService.track_event(
                db=db_session,
                event_type=AnalyticsEventType.VIEW,
                prompt_id=prompt.id,
            )

        for _ in range(3):
            AnalyticsService.track_event(
                db=db_session,
                event_type=AnalyticsEventType.SEARCH,
            )

        headers = self.get_auth_headers(db_session, admin)
        response = client.get(
            "/api/analytics/overview",
            headers=headers,
            params={"days": 30},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total_views"] == 10
        assert data["total_searches"] == 3
        assert data["period_days"] == 30
        assert "top_viewed_prompts" in data
        assert "top_copied_prompts" in data
        assert "daily_activity" in data

    def test_get_overview_analytics_unauthorized(self, client, db_session):
        """Test getting overview analytics without admin access."""
        member = User(
            username="member",
            email="member@example.com",
            full_name="Member User",
            role=UserRole.MEMBER,
        )
        db_session.add(member)
        db_session.commit()

        headers = self.get_auth_headers(db_session, member)
        response = client.get("/api/analytics/overview", headers=headers)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_overview_analytics_unauthenticated(self, client, db_session):
        """Test getting overview analytics without authentication."""
        response = client.get("/api/analytics/overview")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_overview_analytics_with_days_parameter(self, client, db_session):
        """Test getting overview analytics with custom days parameter."""
        admin = User(
            username="admin",
            email="admin@example.com",
            full_name="Admin User",
            role=UserRole.ADMIN,
        )
        db_session.add(admin)
        db_session.commit()

        headers = self.get_auth_headers(db_session, admin)
        response = client.get(
            "/api/analytics/overview",
            headers=headers,
            params={"days": 7},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["period_days"] == 7

