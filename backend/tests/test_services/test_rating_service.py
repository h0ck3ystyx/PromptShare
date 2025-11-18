"""Tests for rating service."""

import pytest
from fastapi import HTTPException, status
from uuid import uuid4

from src.constants import PlatformTag, PromptStatus, UserRole
from src.models.prompt import Prompt
from src.models.rating import Rating
from src.models.user import User
from src.schemas.rating import RatingCreate
from src.services.rating_service import RatingService


class TestRatingService:
    """Test cases for RatingService."""

    def test_create_rating_success(self, db_session):
        """Test creating a rating successfully."""
        # Create author and prompt
        author = User(
            username="testauthor",
            email="testauthor@company.com",
            full_name="Test Author",
            role=UserRole.MEMBER,
        )
        rater = User(
            username="rater",
            email="rater@company.com",
            full_name="Rater User",
            role=UserRole.MEMBER,
        )
        db_session.add_all([author, rater])
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

        # Create rating
        rating_data = RatingCreate(rating=5)

        rating = RatingService.create_or_update_rating(
            db=db_session,
            prompt_id=prompt.id,
            rating_data=rating_data,
            user_id=rater.id,
        )

        assert rating.id is not None
        assert rating.rating == 5
        assert rating.prompt_id == prompt.id
        assert rating.user_id == rater.id

    def test_update_existing_rating(self, db_session):
        """Test updating an existing rating."""
        # Create users
        author = User(
            username="testauthor",
            email="testauthor@company.com",
            full_name="Test Author",
            role=UserRole.MEMBER,
        )
        rater = User(
            username="rater",
            email="rater@company.com",
            full_name="Rater User",
            role=UserRole.MEMBER,
        )
        db_session.add_all([author, rater])
        db_session.commit()

        # Create prompt
        prompt = Prompt(
            title="Test Prompt",
            content="Prompt content",
            platform_tags=[PlatformTag.GITHUB_COPILOT],
            author_id=author.id,
            status=PromptStatus.PUBLISHED,
        )
        db_session.add(prompt)
        db_session.commit()

        # Create initial rating
        rating = Rating(
            prompt_id=prompt.id,
            user_id=rater.id,
            rating=3,
        )
        db_session.add(rating)
        db_session.commit()

        # Update rating
        rating_data = RatingCreate(rating=5)

        updated = RatingService.create_or_update_rating(
            db=db_session,
            prompt_id=prompt.id,
            rating_data=rating_data,
            user_id=rater.id,
        )

        assert updated.id == rating.id
        assert updated.rating == 5

    def test_get_rating_summary(self, db_session):
        """Test getting rating summary."""
        # Create author and prompt
        author = User(
            username="testauthor",
            email="testauthor@company.com",
            full_name="Test Author",
            role=UserRole.MEMBER,
        )
        rater1 = User(
            username="rater1",
            email="rater1@company.com",
            full_name="Rater 1",
            role=UserRole.MEMBER,
        )
        rater2 = User(
            username="rater2",
            email="rater2@company.com",
            full_name="Rater 2",
            role=UserRole.MEMBER,
        )
        db_session.add_all([author, rater1, rater2])
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

        # Create ratings
        rating1 = Rating(prompt_id=prompt.id, user_id=rater1.id, rating=5)
        rating2 = Rating(prompt_id=prompt.id, user_id=rater2.id, rating=3)
        db_session.add_all([rating1, rating2])
        db_session.commit()

        summary = RatingService.get_rating_summary(db_session, prompt.id)

        assert summary["average_rating"] == 4.0
        assert summary["total_ratings"] == 2
        assert summary["rating_distribution"][5] == 1
        assert summary["rating_distribution"][3] == 1

    def test_delete_rating(self, db_session):
        """Test deleting a rating."""
        # Create users
        author = User(
            username="testauthor",
            email="testauthor@company.com",
            full_name="Test Author",
            role=UserRole.MEMBER,
        )
        rater = User(
            username="rater",
            email="rater@company.com",
            full_name="Rater User",
            role=UserRole.MEMBER,
        )
        db_session.add_all([author, rater])
        db_session.commit()

        # Create prompt and rating
        prompt = Prompt(
            title="Test Prompt",
            content="Prompt content",
            platform_tags=[PlatformTag.GITHUB_COPILOT],
            author_id=author.id,
            status=PromptStatus.PUBLISHED,
        )
        db_session.add(prompt)
        db_session.commit()

        rating = Rating(prompt_id=prompt.id, user_id=rater.id, rating=4)
        db_session.add(rating)
        db_session.commit()

        # Delete rating
        RatingService.delete_rating(
            db_session, prompt.id, rater.id
        )

        # Verify deleted
        deleted = (
            db_session.query(Rating)
            .filter(Rating.prompt_id == prompt.id, Rating.user_id == rater.id)
            .first()
        )
        assert deleted is None

