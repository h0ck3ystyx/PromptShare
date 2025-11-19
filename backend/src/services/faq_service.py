"""FAQ service for managing help and frequently asked questions."""

from typing import List, Optional
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from src.constants import UserRole
from src.models.faq import FAQ
from src.models.user import User
from src.schemas.faq import FAQCreate, FAQUpdate


class FAQService:
    """Service for handling FAQ operations."""

    @staticmethod
    def create_faq(
        db: Session,
        faq_data: FAQCreate,
        created_by_id: Optional[UUID] = None,
    ) -> FAQ:
        """
        Create a new FAQ.

        Args:
            db: Database session
            faq_data: FAQ creation data
            created_by_id: Optional ID of the user creating the FAQ

        Returns:
            FAQ: Created FAQ object

        Raises:
            HTTPException: If user not found
        """
        # Verify user exists if provided
        if created_by_id:
            user = db.query(User).filter(User.id == created_by_id).first()
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found",
                )

        # Create FAQ
        faq = FAQ(
            question=faq_data.question,
            answer=faq_data.answer,
            category=faq_data.category,
            display_order=faq_data.display_order,
            is_active=faq_data.is_active,
            created_by_id=created_by_id,
        )

        db.add(faq)
        db.commit()
        db.refresh(faq)
        return faq

    @staticmethod
    def get_faq_by_id(db: Session, faq_id: UUID) -> Optional[FAQ]:
        """
        Get an FAQ by ID.

        Args:
            db: Database session
            faq_id: FAQ ID

        Returns:
            FAQ: FAQ object or None if not found
        """
        return db.query(FAQ).filter(FAQ.id == faq_id).first()

    @staticmethod
    def get_faqs(
        db: Session,
        category: Optional[str] = None,
        active_only: bool = True,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[List[FAQ], int]:
        """
        Get FAQs with optional filters.

        Args:
            db: Database session
            category: Filter by FAQ category
            active_only: Return only active FAQs
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            tuple: (list of FAQs, total count)
        """
        query = db.query(FAQ)

        if active_only:
            query = query.filter(FAQ.is_active == True)

        if category:
            query = query.filter(FAQ.category == category)

        total = query.count()
        faqs = (
            query.order_by(FAQ.display_order, FAQ.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

        return faqs, total

    @staticmethod
    def update_faq(
        db: Session,
        faq_id: UUID,
        faq_data: FAQUpdate,
        user_id: UUID,
    ) -> FAQ:
        """
        Update an FAQ.

        Args:
            db: Database session
            faq_id: FAQ ID
            faq_data: FAQ update data
            user_id: ID of the user updating the FAQ

        Returns:
            FAQ: Updated FAQ object

        Raises:
            HTTPException: If FAQ not found or permission denied
        """
        faq = FAQService.get_faq_by_id(db, faq_id)
        if not faq:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="FAQ not found",
            )

        # Check permissions: creator or admin/moderator
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        if faq.created_by_id != user_id and user.role not in (UserRole.ADMIN, UserRole.MODERATOR):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the creator or admins/moderators can update FAQs",
            )

        # Update fields
        if faq_data.question is not None:
            faq.question = faq_data.question
        if faq_data.answer is not None:
            faq.answer = faq_data.answer
        if faq_data.category is not None:
            faq.category = faq_data.category
        if faq_data.display_order is not None:
            faq.display_order = faq_data.display_order
        if faq_data.is_active is not None:
            faq.is_active = faq_data.is_active

        db.commit()
        db.refresh(faq)
        return faq

    @staticmethod
    def delete_faq(db: Session, faq_id: UUID, user_id: UUID) -> None:
        """
        Delete an FAQ.

        Args:
            db: Database session
            faq_id: FAQ ID
            user_id: ID of the user deleting the FAQ

        Raises:
            HTTPException: If FAQ not found or permission denied
        """
        faq = FAQService.get_faq_by_id(db, faq_id)
        if not faq:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="FAQ not found",
            )

        # Check permissions: creator or admin/moderator
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        if faq.created_by_id != user_id and user.role not in (UserRole.ADMIN, UserRole.MODERATOR):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the creator or admins/moderators can delete FAQs",
            )

        db.delete(faq)
        db.commit()

