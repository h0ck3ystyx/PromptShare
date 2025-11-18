"""User service for user management operations."""

from typing import Optional
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func, or_

from src.constants import UserRole
from src.models.user import User
from src.models.prompt import Prompt
from src.models.comment import Comment
from src.models.rating import Rating
from src.models.upvote import Upvote
from src.schemas.user import UserUpdate


class UserService:
    """Service for handling user management operations."""

    @staticmethod
    def get_users(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        role_filter: Optional[UserRole] = None,
        is_active: Optional[bool] = None,
        search_query: Optional[str] = None,
    ) -> tuple[list[User], int]:
        """
        Get list of users with filters and pagination.

        Args:
            db: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return
            role_filter: Filter by user role
            is_active: Filter by active status
            search_query: Search in username, email, or full_name

        Returns:
            tuple: (list of users, total count)
        """
        query = db.query(User)

        # Apply filters
        if role_filter:
            query = query.filter(User.role == role_filter)

        if is_active is not None:
            query = query.filter(User.is_active == is_active)

        if search_query:
            search_pattern = f"%{search_query}%"
            query = query.filter(
                or_(
                    User.username.ilike(search_pattern),
                    User.email.ilike(search_pattern),
                    User.full_name.ilike(search_pattern),
                )
            )

        # Get total count before pagination
        total = query.count()

        # Apply pagination and ordering
        users = query.order_by(User.created_at.desc()).offset(skip).limit(limit).all()

        return users, total

    @staticmethod
    def get_user_by_id(db: Session, user_id: UUID) -> Optional[User]:
        """
        Get user by ID.

        Args:
            db: Database session
            user_id: User UUID

        Returns:
            Optional[User]: User object if found, None otherwise
        """
        return db.query(User).filter(User.id == user_id).first()

    @staticmethod
    def update_user_role(
        db: Session,
        user_id: UUID,
        new_role: UserRole,
        admin_user: User,
    ) -> User:
        """
        Update user role (admin only).

        Args:
            db: Database session
            user_id: User UUID to update
            new_role: New role to assign
            admin_user: Admin user making the change

        Returns:
            User: Updated user object

        Raises:
            HTTPException: If user not found, unauthorized, or invalid role
        """
        # Verify admin
        if admin_user.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admins can update user roles",
            )

        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        # Prevent admin from changing their own role
        if user.id == admin_user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot change your own role",
            )

        user.role = new_role
        db.commit()
        db.refresh(user)

        return user

    @staticmethod
    def update_user_status(
        db: Session,
        user_id: UUID,
        is_active: bool,
        admin_user: User,
    ) -> User:
        """
        Activate or deactivate user (admin only).

        Args:
            db: Database session
            user_id: User UUID to update
            is_active: New active status
            admin_user: Admin user making the change

        Returns:
            User: Updated user object

        Raises:
            HTTPException: If user not found, unauthorized, or trying to deactivate self
        """
        # Verify admin
        if admin_user.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admins can update user status",
            )

        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        # Prevent admin from deactivating themselves
        if user.id == admin_user.id and not is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot deactivate your own account",
            )

        user.is_active = is_active
        db.commit()
        db.refresh(user)

        return user

    @staticmethod
    def update_user_profile(
        db: Session,
        user_id: UUID,
        user_data: UserUpdate,
        current_user: User,
    ) -> User:
        """
        Update user profile.

        Args:
            db: Database session
            user_id: User UUID to update
            user_data: User update data
            current_user: Current authenticated user

        Returns:
            User: Updated user object

        Raises:
            HTTPException: If user not found, unauthorized, or validation error
        """
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        # Only allow users to update their own profile, or admins to update any profile
        if user.id != current_user.id and current_user.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update this user",
            )

        # Regular users cannot change role or is_active
        if user.id == current_user.id and current_user.role != UserRole.ADMIN:
            if user_data.role is not None or user_data.is_active is not None:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Cannot change role or status",
                )

        # Self-protection: Prevent admins from changing their own role
        if user_data.role is not None and current_user.role == UserRole.ADMIN:
            if user.id == current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot change your own role",
                )

        # Self-protection: Prevent admins from deactivating themselves
        if user_data.is_active is not None and current_user.role == UserRole.ADMIN:
            if user.id == current_user.id and not user_data.is_active:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot deactivate your own account",
                )

        # Update fields
        if user_data.email is not None:
            # Check if email is already taken by another user
            existing_user = db.query(User).filter(
                User.email == user_data.email, User.id != user_id
            ).first()
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already in use",
                )
            user.email = user_data.email

        if user_data.username is not None:
            # Check if username is already taken by another user
            existing_user = db.query(User).filter(
                User.username == user_data.username, User.id != user_id
            ).first()
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Username already in use",
                )
            user.username = user_data.username

        if user_data.full_name is not None:
            user.full_name = user_data.full_name

        if user_data.role is not None and current_user.role == UserRole.ADMIN:
            user.role = user_data.role

        if user_data.is_active is not None and current_user.role == UserRole.ADMIN:
            user.is_active = user_data.is_active

        db.commit()
        db.refresh(user)

        return user

    @staticmethod
    def get_user_stats(db: Session, user_id: UUID) -> dict:
        """
        Get user statistics (prompts, comments, ratings, upvotes).

        Note: Requires comments, ratings, and upvotes tables to exist.
        Run migration 6067905012bc_add_comments_ratings_upvotes_tables if needed.

        Args:
            db: Database session
            user_id: User UUID

        Returns:
            dict: User statistics

        Raises:
            HTTPException: If user not found or database tables are missing
        """
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        try:
            # Count user's prompts
            prompt_count = db.query(func.count(Prompt.id)).filter(
                Prompt.author_id == user_id
            ).scalar() or 0

            # Count user's comments
            comment_count = db.query(func.count(Comment.id)).filter(
                Comment.user_id == user_id
            ).scalar() or 0

            # Count user's ratings
            rating_count = db.query(func.count(Rating.id)).filter(
                Rating.user_id == user_id
            ).scalar() or 0

            # Count user's upvotes
            upvote_count = db.query(func.count(Upvote.id)).filter(
                Upvote.user_id == user_id
            ).scalar() or 0

            # Get total views for user's prompts
            total_views = db.query(func.sum(Prompt.view_count)).filter(
                Prompt.author_id == user_id
            ).scalar() or 0

            return {
                "user_id": user_id,
                "prompt_count": prompt_count,
                "comment_count": comment_count,
                "rating_count": rating_count,
                "upvote_count": upvote_count,
                "total_prompt_views": total_views,
            }
        except Exception as e:
            # Handle case where tables don't exist
            error_str = str(e).lower()
            if "does not exist" in error_str or "undefinedtable" in error_str or "relation" in error_str:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Database tables not found. Please run migrations: alembic upgrade head",
                )
            # Re-raise other exceptions
            raise

