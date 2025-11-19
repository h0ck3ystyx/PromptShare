"""Tests for analytics service."""

from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

from src.constants import AnalyticsEventType, PlatformTag, PromptStatus, UserRole
from src.models.analytics_event import AnalyticsEvent
from src.models.prompt import Prompt
from src.models.prompt_copy_event import PromptCopyEvent
from src.models.user import User
from src.services.analytics_service import AnalyticsService


class TestAnalyticsService:
    """Test cases for AnalyticsService."""

    def test_track_event_view(self, db_session):
        """Test tracking a view event."""
        user = User(
            username="testuser",
            email="test@example.com",
            full_name="Test User",
            role=UserRole.MEMBER,
        )
        prompt = Prompt(
            title="Test Prompt",
            content="Test content",
            platform_tags=[PlatformTag.GITHUB_COPILOT],
            author_id=user.id,
            status=PromptStatus.PUBLISHED,
        )
        db_session.add_all([user, prompt])
        db_session.commit()

        event = AnalyticsService.track_event(
            db=db_session,
            event_type=AnalyticsEventType.VIEW,
            prompt_id=prompt.id,
            user_id=user.id,
        )

        assert event is not None
        assert event.id is not None
        assert event.event_type == AnalyticsEventType.VIEW
        assert event.prompt_id == prompt.id
        assert event.user_id == user.id
        assert event.event_metadata is None

    def test_track_event_search(self, db_session):
        """Test tracking a search event with metadata."""
        user = User(
            username="testuser",
            email="test@example.com",
            full_name="Test User",
            role=UserRole.MEMBER,
        )
        db_session.add(user)
        db_session.commit()

        metadata = {
            "query": "test query",
            "platform": PlatformTag.GITHUB_COPILOT.value,
        }

        event = AnalyticsService.track_event(
            db=db_session,
            event_type=AnalyticsEventType.SEARCH,
            prompt_id=None,
            user_id=user.id,
            metadata=metadata,
        )

        assert event is not None
        assert event.event_type == AnalyticsEventType.SEARCH
        assert event.prompt_id is None
        assert event.user_id == user.id
        assert event.event_metadata == metadata

    def test_track_event_copy(self, db_session):
        """Test tracking a copy event."""
        user = User(
            username="testuser",
            email="test@example.com",
            full_name="Test User",
            role=UserRole.MEMBER,
        )
        prompt = Prompt(
            title="Test Prompt",
            content="Test content",
            platform_tags=[PlatformTag.GITHUB_COPILOT],
            author_id=user.id,
            status=PromptStatus.PUBLISHED,
        )
        db_session.add_all([user, prompt])
        db_session.commit()

        event = AnalyticsService.track_event(
            db=db_session,
            event_type=AnalyticsEventType.COPY,
            prompt_id=prompt.id,
            user_id=user.id,
            metadata={"platform_tag": "github_copilot"},
        )

        assert event is not None
        assert event.event_type == AnalyticsEventType.COPY
        assert event.prompt_id == prompt.id
        assert event.user_id == user.id

    def test_get_prompt_analytics(self, db_session):
        """Test getting analytics for a specific prompt."""
        user = User(
            username="testuser",
            email="test@example.com",
            full_name="Test User",
            role=UserRole.MEMBER,
        )
        prompt = Prompt(
            title="Test Prompt",
            content="Test content",
            platform_tags=[PlatformTag.GITHUB_COPILOT],
            author_id=user.id,
            status=PromptStatus.PUBLISHED,
        )
        db_session.add_all([user, prompt])
        db_session.commit()

        # Create some view events
        for _ in range(5):
            AnalyticsService.track_event(
                db=db_session,
                event_type=AnalyticsEventType.VIEW,
                prompt_id=prompt.id,
            )

        # Create some copy events
        for _ in range(3):
            copy_event = PromptCopyEvent(
                prompt_id=prompt.id,
                user_id=user.id,
            )
            db_session.add(copy_event)
        db_session.commit()

        analytics = AnalyticsService.get_prompt_analytics(
            db=db_session,
            prompt_id=prompt.id,
            days=30,
        )

        assert analytics["prompt_id"] == str(prompt.id)
        assert analytics["prompt_title"] == prompt.title
        assert analytics["total_views"] == 5
        assert analytics["total_copies"] == 3
        assert analytics["period_days"] == 30
        assert "views_series" in analytics
        assert "copies_series" in analytics

    def test_get_prompt_analytics_not_found(self, db_session):
        """Test getting analytics for non-existent prompt."""
        with pytest.raises(ValueError, match="not found"):
            AnalyticsService.get_prompt_analytics(
                db=db_session,
                prompt_id=uuid4(),
                days=30,
            )

    def test_get_overview_analytics(self, db_session):
        """Test getting overview analytics."""
        user = User(
            username="testuser",
            email="test@example.com",
            full_name="Test User",
            role=UserRole.MEMBER,
        )
        prompt1 = Prompt(
            title="Prompt 1",
            content="Content 1",
            platform_tags=[PlatformTag.GITHUB_COPILOT],
            author_id=user.id,
            status=PromptStatus.PUBLISHED,
        )
        prompt2 = Prompt(
            title="Prompt 2",
            content="Content 2",
            platform_tags=[PlatformTag.CURSOR],
            author_id=user.id,
            status=PromptStatus.PUBLISHED,
        )
        db_session.add_all([user, prompt1, prompt2])
        db_session.commit()

        # Create various events
        for _ in range(10):
            AnalyticsService.track_event(
                db=db_session,
                event_type=AnalyticsEventType.VIEW,
                prompt_id=prompt1.id,
            )

        for _ in range(5):
            AnalyticsService.track_event(
                db=db_session,
                event_type=AnalyticsEventType.VIEW,
                prompt_id=prompt2.id,
            )

        for _ in range(3):
            AnalyticsService.track_event(
                db=db_session,
                event_type=AnalyticsEventType.SEARCH,
                user_id=user.id,
            )

        for _ in range(2):
            copy_event = PromptCopyEvent(
                prompt_id=prompt1.id,
                user_id=user.id,
            )
            db_session.add(copy_event)
        db_session.commit()

        analytics = AnalyticsService.get_overview_analytics(
            db=db_session,
            days=30,
        )

        assert analytics["total_views"] == 15
        assert analytics["total_copies"] == 2
        assert analytics["total_searches"] == 3
        assert analytics["period_days"] == 30
        assert len(analytics["top_viewed_prompts"]) > 0
        assert len(analytics["top_copied_prompts"]) > 0
        assert analytics["top_viewed_prompts"][0]["prompt_id"] == str(prompt1.id)
        assert analytics["top_viewed_prompts"][0]["view_count"] == 10

    def test_get_overview_analytics_empty(self, db_session):
        """Test getting overview analytics with no events."""
        analytics = AnalyticsService.get_overview_analytics(
            db=db_session,
            days=30,
        )

        assert analytics["total_views"] == 0
        assert analytics["total_copies"] == 0
        assert analytics["total_searches"] == 0
        assert analytics["period_days"] == 30
        assert len(analytics["top_viewed_prompts"]) == 0
        assert len(analytics["top_copied_prompts"]) == 0

