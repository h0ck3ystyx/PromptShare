"""Search service for prompt discovery."""

from typing import Optional
from uuid import UUID

from sqlalchemy import or_
from sqlalchemy.orm import Session

from src.constants import PlatformTag, PromptStatus, SortOrder
from src.models.category import Category
from src.models.prompt import Prompt


class SearchService:
    """Service for handling search operations."""

    @staticmethod
    def search_prompts(
        db: Session,
        query: Optional[str] = None,
        platform_tag: Optional[PlatformTag] = None,
        category_id: Optional[UUID] = None,
        status_filter: Optional[PromptStatus] = None,
        featured_only: bool = False,
        sort_by: SortOrder = SortOrder.NEWEST,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[list[Prompt], int]:
        """
        Search prompts with full-text search and filters.

        Args:
            db: Database session
            query: Search query string (full-text search)
            platform_tag: Filter by platform tag
            category_id: Filter by category ID
            status_filter: Filter by status (None returns all except archived)
            featured_only: Return only featured prompts
            sort_by: Sort order
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            tuple: (list of prompts, total count)
        """
        sql_query = db.query(Prompt)

        # Default: exclude archived prompts unless explicitly requested
        if status_filter is None:
            sql_query = sql_query.filter(Prompt.status != PromptStatus.ARCHIVED)
        else:
            sql_query = sql_query.filter(Prompt.status == status_filter)

        # Text search - using ILIKE for now, can be upgraded to full-text search
        search_pattern = None
        if query:
            # Search across title, description, content, and use_cases array
            search_pattern = f"%{query}%"
            from sqlalchemy import func
            
            # For PostgreSQL arrays, we need to convert to text and search
            # array_to_string converts array to text, then we can use ILIKE
            use_cases_text = func.array_to_string(Prompt.use_cases, " ")
            
            sql_query = sql_query.filter(
                or_(
                    Prompt.title.ilike(search_pattern),
                    Prompt.description.ilike(search_pattern),
                    Prompt.content.ilike(search_pattern),
                    # Search in use_cases array by converting to text
                    use_cases_text.ilike(search_pattern),
                )
            )

        # Apply filters
        if platform_tag:
            # platform_tag is already a PlatformTag enum from the router
            # PostgreSQL array contains check - check if array contains the platform tag
            # Use the same approach as prompt_service - pass enum directly
            sql_query = sql_query.filter(Prompt.platform_tags.contains([platform_tag]))

        if category_id:
            sql_query = sql_query.join(Prompt.categories).filter(Category.id == category_id).distinct()

        if featured_only:
            sql_query = sql_query.filter(Prompt.is_featured.is_(True))

        # Get total count before pagination
        # For queries with DISTINCT (category joins), count distinct IDs
        if category_id:
            # When using distinct with joins, count distinct IDs
            total = sql_query.with_entities(Prompt.id).distinct().count()
        else:
            total = sql_query.count()

        # Apply sorting - do this after filters to avoid DISTINCT/ORDER BY issues
        if search_pattern:
            # When searching, order by relevance (title matches first)
            # But avoid computed expressions in ORDER BY when using DISTINCT
            if category_id:
                # With DISTINCT, we can't use computed ORDER BY expressions
                # Just use the standard sorting
                sql_query = SearchService._apply_sorting(sql_query, sort_by)
            else:
                # Without DISTINCT, we can use computed relevance ordering
                sql_query = sql_query.order_by(
                    (Prompt.title.ilike(search_pattern)).desc(),
                    *SearchService._get_sort_columns(sort_by)
                )
        else:
            # Apply user's preferred sorting
            sql_query = SearchService._apply_sorting(sql_query, sort_by)
        
        # Apply pagination
        prompts = sql_query.offset(skip).limit(limit).all()

        return prompts, total

    @staticmethod
    def _apply_sorting(query, sort_by: SortOrder):
        """Apply sorting to query based on sort order."""
        sort_columns = SearchService._get_sort_columns(sort_by)
        return query.order_by(*sort_columns)

    @staticmethod
    def _get_sort_columns(sort_by: SortOrder):
        """Get sort columns for a given sort order."""
        if sort_by == SortOrder.NEWEST:
            return [Prompt.created_at.desc()]
        elif sort_by == SortOrder.OLDEST:
            return [Prompt.created_at.asc()]
        elif sort_by == SortOrder.MOST_VIEWED:
            return [Prompt.view_count.desc(), Prompt.created_at.desc()]
        elif sort_by == SortOrder.LEAST_VIEWED:
            return [Prompt.view_count.asc(), Prompt.created_at.desc()]
        elif sort_by == SortOrder.HIGHEST_RATED:
            # Ratings not yet implemented in Phase 4
            # Raise error to prevent misleading behavior
            raise ValueError(
                "Sorting by 'highest_rated' is not yet available. "
                "Ratings will be implemented in Phase 4. "
                "Please use 'newest', 'oldest', 'most_viewed', or 'least_viewed'."
            )
        elif sort_by == SortOrder.LOWEST_RATED:
            # Ratings not yet implemented in Phase 4
            # Raise error to prevent misleading behavior
            raise ValueError(
                "Sorting by 'lowest_rated' is not yet available. "
                "Ratings will be implemented in Phase 4. "
                "Please use 'newest', 'oldest', 'most_viewed', or 'least_viewed'."
            )
        else:
            # Default to newest
            return [Prompt.created_at.desc()]

