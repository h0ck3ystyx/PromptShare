"""Upvote service for business logic."""

from typing import Optional
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from src.models.prompt import Prompt
from src.models.upvote import Upvote
from src.models.user import User


class UpvoteService:
    """Service for handling upvote operations."""

    @staticmethod
    def toggle_upvote(
        db: Session,
        prompt_id: UUID,
        user_id: UUID,
    ) -> tuple[Upvote | None, bool]:
        """
        Toggle upvote for a prompt (add if not exists, remove if exists).

        Args:
            db: Database session
            prompt_id: Prompt UUID
            user_id: ID of the user upvoting

        Returns:
            tuple: (Upvote object if added, None if removed, is_upvoted boolean)

        Raises:
            HTTPException: If prompt not found
        """
        # Verify prompt exists
        prompt = db.query(Prompt).filter(Prompt.id == prompt_id).first()
        if not prompt:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Prompt not found",
            )

        # Check if upvote already exists
        existing_upvote = (
            db.query(Upvote)
            .filter(Upvote.prompt_id == prompt_id, Upvote.user_id == user_id)
            .first()
        )

        if existing_upvote:
            # Remove upvote
            db.delete(existing_upvote)
            db.commit()
            return None, False
        else:
            # Add upvote
            upvote = Upvote(
                prompt_id=prompt_id,
                user_id=user_id,
            )
            db.add(upvote)
            db.commit()
            db.refresh(upvote)
            return upvote, True

    @staticmethod
    def get_upvote(
        db: Session,
        prompt_id: UUID,
        user_id: UUID,
    ) -> Optional[Upvote]:
        """
        Get a user's upvote for a prompt.

        Args:
            db: Database session
            prompt_id: Prompt UUID
            user_id: User UUID

        Returns:
            Upvote: Upvote object if found, None otherwise
        """
        return (
            db.query(Upvote)
            .filter(Upvote.prompt_id == prompt_id, Upvote.user_id == user_id)
            .first()
        )

    @staticmethod
    def get_upvote_count(db: Session, prompt_id: UUID) -> int:
        """
        Get total upvote count for a prompt.

        Args:
            db: Database session
            prompt_id: Prompt UUID

        Returns:
            int: Total number of upvotes
        """
        from sqlalchemy import func

        count = (
            db.query(func.count(Upvote.id))
            .filter(Upvote.prompt_id == prompt_id)
            .scalar()
        )
        return count or 0

    @staticmethod
    def has_user_upvoted(
        db: Session,
        prompt_id: UUID,
        user_id: UUID,
    ) -> bool:
        """
        Check if a user has upvoted a prompt.

        Args:
            db: Database session
            prompt_id: Prompt UUID
            user_id: User UUID

        Returns:
            bool: True if user has upvoted, False otherwise
        """
        upvote = UpvoteService.get_upvote(db, prompt_id, user_id)
        return upvote is not None

