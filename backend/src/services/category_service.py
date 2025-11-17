"""Category service for business logic."""

from typing import Optional
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from src.constants import UserRole
from src.models.category import Category
from src.models.user import User
from src.schemas.category import CategoryCreate, CategoryUpdate


class CategoryService:
    """Service for handling category operations."""

    @staticmethod
    def create_category(
        db: Session,
        category_data: CategoryCreate,
        user: User,
    ) -> Category:
        """
        Create a new category (admin/moderator only).

        Args:
            db: Database session
            category_data: Category creation data
            user: Current user (must be admin or moderator)

        Returns:
            Category: Created category object

        Raises:
            HTTPException: If user lacks permission or category already exists
        """
        # Check permissions
        if user.role not in (UserRole.ADMIN, UserRole.MODERATOR):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admins and moderators can create categories",
            )

        # Check if category with same name or slug already exists
        existing = (
            db.query(Category)
            .filter(
                (Category.name == category_data.name) | (Category.slug == category_data.slug)
            )
            .first()
        )

        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Category with name '{category_data.name}' or slug '{category_data.slug}' already exists",
            )

        category = Category(
            name=category_data.name,
            description=category_data.description,
            slug=category_data.slug,
        )

        db.add(category)
        db.commit()
        db.refresh(category)
        return category

    @staticmethod
    def get_category_by_id(db: Session, category_id: UUID) -> Optional[Category]:
        """
        Get category by ID.

        Args:
            db: Database session
            category_id: Category UUID

        Returns:
            Category: Category object if found, None otherwise
        """
        return db.query(Category).filter(Category.id == category_id).first()

    @staticmethod
    def get_category_by_slug(db: Session, slug: str) -> Optional[Category]:
        """
        Get category by slug.

        Args:
            db: Database session
            slug: Category slug

        Returns:
            Category: Category object if found, None otherwise
        """
        return db.query(Category).filter(Category.slug == slug).first()

    @staticmethod
    def get_categories(
        db: Session,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[list[Category], int]:
        """
        Get list of categories with pagination.

        Args:
            db: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            tuple: (list of categories, total count)
        """
        query = db.query(Category)

        total = query.count()

        categories = (
            query.order_by(Category.name.asc())
            .offset(skip)
            .limit(limit)
            .all()
        )

        return categories, total

    @staticmethod
    def update_category(
        db: Session,
        category_id: UUID,
        category_data: CategoryUpdate,
        user: User,
    ) -> Category:
        """
        Update an existing category (admin/moderator only).

        Args:
            db: Database session
            category_id: Category UUID
            category_data: Category update data
            user: Current user (must be admin or moderator)

        Returns:
            Category: Updated category object

        Raises:
            HTTPException: If category not found or user lacks permission
        """
        # Check permissions
        if user.role not in (UserRole.ADMIN, UserRole.MODERATOR):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admins and moderators can update categories",
            )

        category = db.query(Category).filter(Category.id == category_id).first()

        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found",
            )

        # Check for conflicts if name or slug is being updated
        if category_data.name is not None or category_data.slug is not None:
            name = category_data.name if category_data.name is not None else category.name
            slug = category_data.slug if category_data.slug is not None else category.slug

            existing = (
                db.query(Category)
                .filter(
                    (Category.id != category_id)
                    & ((Category.name == name) | (Category.slug == slug))
                )
                .first()
            )

            if existing:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Category with name '{name}' or slug '{slug}' already exists",
                )

        # Update fields
        if category_data.name is not None:
            category.name = category_data.name
        if category_data.description is not None:
            category.description = category_data.description
        if category_data.slug is not None:
            category.slug = category_data.slug

        db.commit()
        db.refresh(category)
        return category

    @staticmethod
    def delete_category(
        db: Session,
        category_id: UUID,
        user: User,
    ) -> None:
        """
        Delete a category (admin only).

        Args:
            db: Database session
            category_id: Category UUID
            user: Current user (must be admin)

        Raises:
            HTTPException: If category not found or user lacks permission
        """
        # Check permissions (only admin can delete)
        if user.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admins can delete categories",
            )

        category = db.query(Category).filter(Category.id == category_id).first()

        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found",
            )

        # Check if category is in use
        if category.prompts:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Cannot delete category that is associated with prompts",
            )

        db.delete(category)
        db.commit()

