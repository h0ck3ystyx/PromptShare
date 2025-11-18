"""Rating service for business logic."""

from typing import Optional
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from src.models.prompt import Prompt
from src.models.rating import Rating
from src.models.user import User
from src.schemas.rating import RatingCreate, RatingUpdate


class RatingService:
    """Service for handling rating operations."""

    @staticmethod
    def create_or_update_rating(
        db: Session,
        prompt_id: UUID,
        rating_data: RatingCreate,
        user_id: UUID,
    ) -> Rating:
        """
        Create or update a rating for a prompt.

        Args:
            db: Database session
            prompt_id: Prompt UUID
            rating_data: Rating data
            user_id: ID of the user creating/updating the rating

        Returns:
            Rating: Created or updated rating object

        Raises:
            HTTPException: If prompt not found or rating is invalid
        """
        # Verify prompt exists
        prompt = db.query(Prompt).filter(Prompt.id == prompt_id).first()
        if not prompt:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Prompt not found",
            )

        # Check if rating already exists
        existing_rating = (
            db.query(Rating)
            .filter(Rating.prompt_id == prompt_id, Rating.user_id == user_id)
            .first()
        )

        from sqlalchemy.orm import joinedload
        
        if existing_rating:
            # Update existing rating
            existing_rating.rating = rating_data.rating
            db.commit()
            # Reload with user relationship
            db.refresh(existing_rating)
            rating_with_user = (
                db.query(Rating)
                .options(joinedload(Rating.user))
                .filter(Rating.id == existing_rating.id)
                .first()
            )
            return rating_with_user or existing_rating
        else:
            # Create new rating
            rating = Rating(
                prompt_id=prompt_id,
                user_id=user_id,
                rating=rating_data.rating,
            )
            db.add(rating)
            db.commit()
            # Reload with user relationship
            rating_with_user = (
                db.query(Rating)
                .options(joinedload(Rating.user))
                .filter(Rating.id == rating.id)
                .first()
            )
            return rating_with_user or rating

    @staticmethod
    def get_rating(
        db: Session,
        prompt_id: UUID,
        user_id: UUID,
    ) -> Optional[Rating]:
        """
        Get a user's rating for a prompt.

        Args:
            db: Database session
            prompt_id: Prompt UUID
            user_id: User UUID

        Returns:
            Rating: Rating object if found, None otherwise
        """
        from sqlalchemy.orm import joinedload
        return (
            db.query(Rating)
            .options(joinedload(Rating.user))
            .filter(Rating.prompt_id == prompt_id, Rating.user_id == user_id)
            .first()
        )

    @staticmethod
    def delete_rating(
        db: Session,
        prompt_id: UUID,
        user_id: UUID,
    ) -> None:
        """
        Delete a user's rating for a prompt.

        Args:
            db: Database session
            prompt_id: Prompt UUID
            user_id: User UUID

        Raises:
            HTTPException: If rating not found
        """
        rating = (
            db.query(Rating)
            .filter(Rating.prompt_id == prompt_id, Rating.user_id == user_id)
            .first()
        )

        if not rating:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Rating not found",
            )

        db.delete(rating)
        db.commit()

    @staticmethod
    def get_rating_summary(db: Session, prompt_id: UUID) -> dict:
        """
        Get rating summary for a prompt.

        Args:
            db: Database session
            prompt_id: Prompt UUID

        Returns:
            dict: Rating summary with average, total, and distribution
        """
        ratings = db.query(Rating).filter(Rating.prompt_id == prompt_id).all()

        if not ratings:
            return {
                "prompt_id": prompt_id,
                "average_rating": 0.0,
                "total_ratings": 0,
                "rating_distribution": {1: 0, 2: 0, 3: 0, 4: 0, 5: 0},
            }

        total = len(ratings)
        average = sum(r.rating for r in ratings) / total

        # Calculate distribution
        distribution = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        for rating in ratings:
            distribution[rating.rating] = distribution.get(rating.rating, 0) + 1

        return {
            "prompt_id": prompt_id,
            "average_rating": round(average, 2),
            "total_ratings": total,
            "rating_distribution": distribution,
        }

