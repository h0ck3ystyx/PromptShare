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
        if query:
            # Search across title, description, and content
            search_pattern = f"%{query}%"
            sql_query = sql_query.filter(
                or_(
                    Prompt.title.ilike(search_pattern),
                    Prompt.description.ilike(search_pattern),
                    Prompt.content.ilike(search_pattern),
                )
            )
            # When searching, order by relevance (title matches first, then description, then content)
            # This is a simple relevance - can be enhanced with full-text search later
            sql_query = sql_query.order_by(
                # Prioritize title matches
                (Prompt.title.ilike(search_pattern)).desc(),
                # Then apply user's preferred sorting
                *SearchService._get_sort_columns(sort_by)
            )
        else:
            # Apply sorting when not searching
            sql_query = SearchService._apply_sorting(sql_query, sort_by)

        # Apply filters
        if platform_tag:
            try:
                sql_query = sql_query.filter(Prompt.platform_tags.contains([platform_tag]))
            except ValueError:
                # If invalid platform tag, return empty results
                sql_query = sql_query.filter(False)

        if category_id:
            sql_query = sql_query.join(Prompt.categories).filter(Category.id == category_id).distinct()

        if featured_only:
            sql_query = sql_query.filter(Prompt.is_featured.is_(True))

        # Get total count before pagination
        total = sql_query.count()

        # Apply pagination
        if query:
            # When searching, we already have ordering by relevance
            # But we need to re-apply sorting after getting results if needed
            # For now, keep relevance-based ordering for search results
            prompts = sql_query.offset(skip).limit(limit).all()
        else:
            # Apply sorting and pagination
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
            # TODO: Implement when ratings are added in Phase 4
            # For now, fall back to newest
            return [Prompt.created_at.desc()]
        elif sort_by == SortOrder.LOWEST_RATED:
            # TODO: Implement when ratings are added in Phase 4
            # For now, fall back to newest
            return [Prompt.created_at.desc()]
        else:
            # Default to newest
            return [Prompt.created_at.desc()]

