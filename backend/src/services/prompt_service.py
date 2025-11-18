"""Prompt service for business logic."""

from typing import Optional
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from src.constants import PlatformTag, PromptStatus, UserRole
from src.models.category import Category
from src.models.prompt import Prompt
from src.models.prompt_copy_event import PromptCopyEvent
from src.models.user import User
from src.schemas.prompt import PromptCreate, PromptUpdate


class PromptService:
    """Service for handling prompt operations."""

    @staticmethod
    def create_prompt(
        db: Session,
        prompt_data: PromptCreate,
        author_id: UUID,
    ) -> Prompt:
        """
        Create a new prompt.

        Args:
            db: Database session
            prompt_data: Prompt creation data
            author_id: ID of the user creating the prompt

        Returns:
            Prompt: Created prompt object

        Raises:
            HTTPException: If categories not found or other validation errors
        """
        # Validate categories if provided
        if prompt_data.category_ids:
            categories = (
                db.query(Category)
                .filter(Category.id.in_(prompt_data.category_ids))
                .all()
            )
            if len(categories) != len(prompt_data.category_ids):
                found_ids = {cat.id for cat in categories}
                missing_ids = set(prompt_data.category_ids) - found_ids
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Categories not found: {list(missing_ids)}",
                )

        # Create prompt
        prompt = Prompt(
            title=prompt_data.title,
            description=prompt_data.description,
            content=prompt_data.content,
            platform_tags=prompt_data.platform_tags,
            use_cases=prompt_data.use_cases,
            usage_tips=prompt_data.usage_tips,
            status=prompt_data.status,
            author_id=author_id,
        )

        # Associate categories
        if prompt_data.category_ids and categories:
            prompt.categories = categories

        db.add(prompt)
        db.commit()
        db.refresh(prompt)
        return prompt

    @staticmethod
    def get_prompt_by_id(db: Session, prompt_id: UUID, increment_view: bool = False) -> Optional[Prompt]:
        """
        Get prompt by ID.

        Args:
            db: Database session
            prompt_id: Prompt UUID
            increment_view: Whether to increment view count

        Returns:
            Prompt: Prompt object if found, None otherwise
        """
        prompt = db.query(Prompt).filter(Prompt.id == prompt_id).first()

        if prompt and increment_view:
            prompt.view_count += 1
            db.commit()
            db.refresh(prompt)

        return prompt

    @staticmethod
    def get_prompts(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        status_filter: Optional[PromptStatus] = None,
        platform_tag: Optional[str] = None,
        category_id: Optional[UUID] = None,
        author_id: Optional[UUID] = None,
        featured_only: bool = False,
        search_query: Optional[str] = None,
        title_search: Optional[str] = None,
        content_search: Optional[str] = None,
    ) -> tuple[list[Prompt], int]:
        """
        Get list of prompts with filters and pagination.

        Args:
            db: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return
            status_filter: Filter by status (None returns all except archived)
            platform_tag: Filter by platform tag
            category_id: Filter by category ID
            author_id: Filter by author ID
            featured_only: Return only featured prompts
            search_query: Keyword search across title, description, and content
            title_search: Search in title field
            content_search: Search in content field

        Returns:
            tuple: (list of prompts, total count)
        """
        query = db.query(Prompt)

        # Default: exclude archived prompts unless explicitly requested
        if status_filter is None:
            query = query.filter(Prompt.status != PromptStatus.ARCHIVED)
        else:
            query = query.filter(Prompt.status == status_filter)

        # Apply filters
        if platform_tag:
            # PostgreSQL array contains check - check if array contains the platform tag
            # SQLAlchemy's contains uses PostgreSQL's @> operator for array containment
            # We need to pass a list with the enum value (platform_tag is already a string from enum.value)
            # Convert string back to enum for proper type matching
            try:
                platform_enum = PlatformTag(platform_tag)
                query = query.filter(Prompt.platform_tags.contains([platform_enum]))
            except ValueError:
                # If invalid platform tag, return empty results
                query = query.filter(False)

        if category_id:
            query = query.join(Prompt.categories).filter(Category.id == category_id).distinct()

        if author_id:
            query = query.filter(Prompt.author_id == author_id)

        if featured_only:
            query = query.filter(Prompt.is_featured.is_(True))

        # Text search filters
        if search_query:
            # Search across title, description, and content
            search_pattern = f"%{search_query}%"
            query = query.filter(
                or_(
                    Prompt.title.ilike(search_pattern),
                    Prompt.description.ilike(search_pattern),
                    Prompt.content.ilike(search_pattern),
                )
            )
        
        if title_search:
            query = query.filter(Prompt.title.ilike(f"%{title_search}%"))
        
        if content_search:
            query = query.filter(Prompt.content.ilike(f"%{content_search}%"))

        # Get total count before pagination
        total = query.count()

        # Apply pagination and ordering
        prompts = (
            query.order_by(Prompt.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

        return prompts, total

    @staticmethod
    def update_prompt(
        db: Session,
        prompt_id: UUID,
        prompt_data: PromptUpdate,
        user: User,
    ) -> Prompt:
        """
        Update an existing prompt.

        Args:
            db: Database session
            prompt_id: Prompt UUID
            prompt_data: Prompt update data
            user: Current user (must be author or admin)

        Returns:
            Prompt: Updated prompt object

        Raises:
            HTTPException: If prompt not found or user lacks permission
        """
        prompt = db.query(Prompt).filter(Prompt.id == prompt_id).first()

        if not prompt:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Prompt not found",
            )

        # Check permissions: author or admin can update
        if prompt.author_id != user.id and user.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update this prompt",
            )

        # Update fields
        if prompt_data.title is not None:
            prompt.title = prompt_data.title
        if prompt_data.description is not None:
            prompt.description = prompt_data.description
        if prompt_data.content is not None:
            prompt.content = prompt_data.content
        if prompt_data.platform_tags is not None:
            prompt.platform_tags = prompt_data.platform_tags
        if prompt_data.use_cases is not None:
            prompt.use_cases = prompt_data.use_cases
        if prompt_data.usage_tips is not None:
            prompt.usage_tips = prompt_data.usage_tips
        if prompt_data.status is not None:
            prompt.status = prompt_data.status

        # Update categories if provided
        if prompt_data.category_ids is not None:
            categories = (
                db.query(Category)
                .filter(Category.id.in_(prompt_data.category_ids))
                .all()
            )
            if len(categories) != len(prompt_data.category_ids):
                found_ids = {cat.id for cat in categories}
                missing_ids = set(prompt_data.category_ids) - found_ids
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Categories not found: {list(missing_ids)}",
                )
            prompt.categories = categories

        db.commit()
        db.refresh(prompt)
        return prompt

    @staticmethod
    def delete_prompt(
        db: Session,
        prompt_id: UUID,
        user: User,
    ) -> None:
        """
        Delete a prompt.

        Args:
            db: Database session
            prompt_id: Prompt UUID
            user: Current user (must be author or admin)

        Raises:
            HTTPException: If prompt not found or user lacks permission
        """
        prompt = db.query(Prompt).filter(Prompt.id == prompt_id).first()

        if not prompt:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Prompt not found",
            )

        # Check permissions: author or admin can delete
        if prompt.author_id != user.id and user.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to delete this prompt",
            )

        db.delete(prompt)
        db.commit()

    @staticmethod
    def track_copy(
        db: Session,
        prompt_id: UUID,
        user_id: Optional[UUID] = None,
        platform_tag: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> None:
        """
        Track a prompt copy event (for analytics).

        Args:
            db: Database session
            prompt_id: Prompt UUID
            user_id: Optional user ID if authenticated
            platform_tag: Optional platform tag context
            ip_address: Optional IP address of the requester
            user_agent: Optional user agent string

        Raises:
            HTTPException: If prompt not found
        """
        prompt = db.query(Prompt).filter(Prompt.id == prompt_id).first()

        if not prompt:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Prompt not found",
            )

        # Create and persist copy event
        copy_event = PromptCopyEvent(
            prompt_id=prompt_id,
            user_id=user_id,
            platform_tag=platform_tag,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        db.add(copy_event)
        
        # Increment view count as engagement metric
        prompt.view_count += 1
        
        db.commit()

