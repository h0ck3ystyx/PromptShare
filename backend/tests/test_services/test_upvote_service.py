"""Tests for upvote service."""

import pytest
from uuid import uuid4

from src.constants import PlatformTag, PromptStatus, UserRole
from src.models.prompt import Prompt
from src.models.upvote import Upvote
from src.models.user import User
from src.services.upvote_service import UpvoteService


class TestUpvoteService:
    """Test cases for UpvoteService."""

    def test_toggle_upvote_add(self, db_session):
        """Test adding an upvote."""
        # Create author and prompt
        author = User(
            username="testauthor",
            email="testauthor@company.com",
            full_name="Test Author",
            role=UserRole.MEMBER,
        )
        voter = User(
            username="voter",
            email="voter@company.com",
            full_name="Voter User",
            role=UserRole.MEMBER,
        )
        db_session.add_all([author, voter])
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

        # Add upvote
        upvote, is_upvoted = UpvoteService.toggle_upvote(
            db=db_session,
            prompt_id=prompt.id,
            user_id=voter.id,
        )

        assert upvote is not None
        assert is_upvoted is True
        assert upvote.prompt_id == prompt.id
        assert upvote.user_id == voter.id

    def test_toggle_upvote_remove(self, db_session):
        """Test removing an upvote."""
        # Create users
        author = User(
            username="testauthor",
            email="testauthor@company.com",
            full_name="Test Author",
            role=UserRole.MEMBER,
        )
        voter = User(
            username="voter",
            email="voter@company.com",
            full_name="Voter User",
            role=UserRole.MEMBER,
        )
        db_session.add_all([author, voter])
        db_session.commit()

        # Create prompt and upvote
        prompt = Prompt(
            title="Test Prompt",
            content="Prompt content",
            platform_tags=[PlatformTag.GITHUB_COPILOT],
            author_id=author.id,
            status=PromptStatus.PUBLISHED,
        )
        db_session.add(prompt)
        db_session.commit()

        upvote = Upvote(prompt_id=prompt.id, user_id=voter.id)
        db_session.add(upvote)
        db_session.commit()

        # Remove upvote
        result, is_upvoted = UpvoteService.toggle_upvote(
            db=db_session,
            prompt_id=prompt.id,
            user_id=voter.id,
        )

        assert result is None
        assert is_upvoted is False

        # Verify removed
        deleted = (
            db_session.query(Upvote)
            .filter(Upvote.prompt_id == prompt.id, Upvote.user_id == voter.id)
            .first()
        )
        assert deleted is None

    def test_get_upvote_count(self, db_session):
        """Test getting upvote count."""
        # Create users
        author = User(
            username="testauthor",
            email="testauthor@company.com",
            full_name="Test Author",
            role=UserRole.MEMBER,
        )
        voter1 = User(
            username="voter1",
            email="voter1@company.com",
            full_name="Voter 1",
            role=UserRole.MEMBER,
        )
        voter2 = User(
            username="voter2",
            email="voter2@company.com",
            full_name="Voter 2",
            role=UserRole.MEMBER,
        )
        db_session.add_all([author, voter1, voter2])
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

        # Create upvotes
        upvote1 = Upvote(prompt_id=prompt.id, user_id=voter1.id)
        upvote2 = Upvote(prompt_id=prompt.id, user_id=voter2.id)
        db_session.add_all([upvote1, upvote2])
        db_session.commit()

        count = UpvoteService.get_upvote_count(db_session, prompt.id)
        assert count == 2

    def test_has_user_upvoted(self, db_session):
        """Test checking if user has upvoted."""
        # Create users
        author = User(
            username="testauthor",
            email="testauthor@company.com",
            full_name="Test Author",
            role=UserRole.MEMBER,
        )
        voter = User(
            username="voter",
            email="voter@company.com",
            full_name="Voter User",
            role=UserRole.MEMBER,
        )
        db_session.add_all([author, voter])
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

        # Check before upvoting
        has_upvoted = UpvoteService.has_user_upvoted(
            db_session, prompt.id, voter.id
        )
        assert has_upvoted is False

        # Add upvote
        upvote = Upvote(prompt_id=prompt.id, user_id=voter.id)
        db_session.add(upvote)
        db_session.commit()

        # Check after upvoting
        has_upvoted = UpvoteService.has_user_upvoted(
            db_session, prompt.id, voter.id
        )
        assert has_upvoted is True

