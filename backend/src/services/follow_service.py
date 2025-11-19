"""Follow service for managing category follows."""

from typing import Optional
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from src.models.category import Category
from src.models.user import User
from src.models.user_follow import UserFollow


class FollowService:
    """Service for handling follow operations."""

    @staticmethod
    def follow_category(
        db: Session,
        user_id: UUID,
        category_id: UUID,
    ) -> UserFollow:
        """
        Follow a category.

        Args:
            db: Database session
            user_id: ID of the user following
            category_id: ID of the category to follow

        Returns:
            UserFollow: The created follow relationship

        Raises:
            HTTPException: If category not found or already following
        """
        # Verify category exists
        category = db.query(Category).filter(Category.id == category_id).first()
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found",
            )

        # Check if already following
        existing_follow = (
            db.query(UserFollow)
            .filter(UserFollow.user_id == user_id, UserFollow.category_id == category_id)
            .first()
        )
        if existing_follow:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Already following this category",
            )

        # Create follow relationship
        follow = UserFollow(user_id=user_id, category_id=category_id)
        db.add(follow)
        db.commit()
        db.refresh(follow)

        return follow

    @staticmethod
    def unfollow_category(
        db: Session,
        user_id: UUID,
        category_id: UUID,
    ) -> None:
        """
        Unfollow a category.

        Args:
            db: Database session
            user_id: ID of the user unfollowing
            category_id: ID of the category to unfollow

        Raises:
            HTTPException: If not following this category
        """
        follow = (
            db.query(UserFollow)
            .filter(UserFollow.user_id == user_id, UserFollow.category_id == category_id)
            .first()
        )

        if not follow:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Not following this category",
            )

        db.delete(follow)
        db.commit()

    @staticmethod
    def get_user_follows(
        db: Session,
        user_id: UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[list[Category], int]:
        """
        Get categories followed by a user.

        Args:
            db: Database session
            user_id: ID of the user
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            tuple: (list of categories, total count)
        """
        # Get follow relationships
        follows = (
            db.query(UserFollow)
            .filter(UserFollow.user_id == user_id)
            .order_by(UserFollow.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

        # Extract categories
        categories = [follow.category for follow in follows if follow.category]

        # Get total count
        total = db.query(UserFollow).filter(UserFollow.user_id == user_id).count()

        return categories, total

    @staticmethod
    def is_following_category(
        db: Session,
        user_id: UUID,
        category_id: UUID,
    ) -> bool:
        """
        Check if user is following a category.

        Args:
            db: Database session
            user_id: ID of the user
            category_id: ID of the category

        Returns:
            bool: True if following, False otherwise
        """
        follow = (
            db.query(UserFollow)
            .filter(UserFollow.user_id == user_id, UserFollow.category_id == category_id)
            .first()
        )
        return follow is not None

    @staticmethod
    def get_category_followers(
        db: Session,
        category_id: UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[list[User], int]:
        """
        Get users following a category.

        Args:
            db: Database session
            category_id: ID of the category
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            tuple: (list of users, total count)
        """
        # Get follow relationships
        follows = (
            db.query(UserFollow)
            .filter(UserFollow.category_id == category_id)
            .order_by(UserFollow.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

        # Extract users
        users = [follow.user for follow in follows if follow.user]

        # Get total count
        total = db.query(UserFollow).filter(UserFollow.category_id == category_id).count()

        return users, total

