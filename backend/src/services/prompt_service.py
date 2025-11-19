"""Prompt service for business logic."""

from typing import Optional
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from src.constants import NotificationType, PromptStatus, SortOrder, UserRole
from src.models.category import Category
from src.models.prompt import Prompt
from src.models.prompt_copy_event import PromptCopyEvent
from src.models.user import User
from src.models.user_follow import UserFollow
from src.schemas.prompt import PromptCreate, PromptUpdate


class PromptService:
    """Service for handling prompt operations."""

    @staticmethod
    def create_prompt(
        db: Session,
        prompt_data: PromptCreate,
        author_id: UUID,
        author: Optional[User] = None,
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
        # Get author if not provided
        if author is None:
            author = db.query(User).filter(User.id == author_id).first()
            if not author:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Author not found",
                )

        # Check permission for is_featured
        if prompt_data.is_featured and author.role not in (UserRole.ADMIN, UserRole.MODERATOR):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admins and moderators can set featured status",
            )

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
            is_featured=prompt_data.is_featured if prompt_data.is_featured else False,
        )

        # Associate categories
        if prompt_data.category_ids and categories:
            prompt.categories = categories

        db.add(prompt)
        db.commit()
        db.refresh(prompt)

        # Notify followers if prompt is published
        if prompt.status == PromptStatus.PUBLISHED and prompt.categories:
            PromptService._notify_category_followers(
                db=db,
                prompt=prompt,
                notification_type=NotificationType.NEW_PROMPT,
            )

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
        sort_by: SortOrder = SortOrder.NEWEST,
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
            sort_by: Sort order

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
            from src.constants import PlatformTag
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
            query = query.filter(Prompt.is_featured == True)

        # Text search filters
        from sqlalchemy import or_
        
        if search_query:
            # Search across title, description, content, and use_cases array
            search_pattern = f"%{search_query}%"
            from sqlalchemy import func
            
            # For PostgreSQL arrays, we need to convert to text and search
            # array_to_string converts array to text, then we can use ILIKE
            use_cases_text = func.array_to_string(Prompt.use_cases, " ")
            
            query = query.filter(
                or_(
                    Prompt.title.ilike(search_pattern),
                    Prompt.description.ilike(search_pattern),
                    Prompt.content.ilike(search_pattern),
                    # Search in use_cases array by converting to text
                    use_cases_text.ilike(search_pattern),
                )
            )
        
        if title_search:
            query = query.filter(Prompt.title.ilike(f"%{title_search}%"))
        
        if content_search:
            query = query.filter(Prompt.content.ilike(f"%{content_search}%"))

        # Get total count before pagination
        total = query.count()

        # Apply sorting
        from src.constants import SortOrder
        from src.services.search_service import SearchService
        
        # Convert string to SortOrder enum if needed
        if isinstance(sort_by, str):
            try:
                sort_by = SortOrder(sort_by)
            except ValueError:
                sort_by = SortOrder.NEWEST
        
        query = SearchService._apply_sorting(query, sort_by, db)

        # Apply pagination
        prompts = query.offset(skip).limit(limit).all()

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
        if prompt_data.is_featured is not None:
            # Only admins and moderators can set featured status
            if user.role not in (UserRole.ADMIN, UserRole.MODERATOR):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Only admins and moderators can set featured status",
                )
            prompt.is_featured = prompt_data.is_featured

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

        # Track if status changed to published or if content was updated
        old_status = prompt.status
        status_changed_to_published = (
            prompt_data.status == PromptStatus.PUBLISHED
            and old_status != PromptStatus.PUBLISHED
        )
        content_updated = prompt_data.content is not None

        db.commit()
        db.refresh(prompt)

        # Notify followers if status changed to published
        if status_changed_to_published and prompt.categories:
            PromptService._notify_category_followers(
                db=db,
                prompt=prompt,
                notification_type=NotificationType.NEW_PROMPT,
            )
        # Notify followers if content was updated (and prompt is published)
        elif content_updated and prompt.status == PromptStatus.PUBLISHED and prompt.categories:
            PromptService._notify_category_followers(
                db=db,
                prompt=prompt,
                notification_type=NotificationType.UPDATE,
            )

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
    def _notify_category_followers(
        db: Session,
        prompt: Prompt,
        notification_type: NotificationType,
    ) -> None:
        """
        Notify all users following the prompt's categories.

        Deduplicates notifications so users following multiple categories
        only receive one notification per prompt.

        Args:
            db: Database session
            prompt: The prompt that triggered the notification
            notification_type: Type of notification (NEW_PROMPT or UPDATE)
        """
        from src.services.notification_service import NotificationService

        if not prompt.categories:
            return

        category_ids = [cat.id for cat in prompt.categories]

        # Get all users following these categories
        follows = (
            db.query(UserFollow)
            .filter(UserFollow.category_id.in_(category_ids))
            .all()
        )

        # Deduplicate by user_id - users following multiple categories get one notification
        unique_user_ids = {follow.user_id for follow in follows if follow.user_id != prompt.author_id}

        if not unique_user_ids:
            return

        # Create notification message
        if notification_type == NotificationType.NEW_PROMPT:
            message = f"New prompt published: {prompt.title}"
        else:  # UPDATE
            message = f"Prompt updated: {prompt.title}"

        # Send notifications asynchronously via Celery
        from src.tasks.notifications import send_bulk_notifications_task

        user_id_strings = [str(user_id) for user_id in unique_user_ids]
        
        # Queue async task for notification delivery
        send_bulk_notifications_task.delay(
            user_ids=user_id_strings,
            notification_type=notification_type.value,
            message=message,
            prompt_id=str(prompt.id),
            send_email=settings.email_enabled,
        )

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

