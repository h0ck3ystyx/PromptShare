"""Search router endpoints."""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status

from src.constants import PlatformTag, PromptStatus, SortOrder
from src.dependencies import DatabaseDep
from src.schemas.common import PaginatedResponse
from src.schemas.prompt import PromptResponse
from src.services.search_service import SearchService

router = APIRouter(prefix="/search", tags=["search"])


@router.get(
    "",
    response_model=PaginatedResponse[PromptResponse],
    summary="Search prompts with full-text search and filters",
)
async def search_prompts(
    db: DatabaseDep,
    q: Optional[str] = Query(None, description="Search query string"),
    platform: Optional[PlatformTag] = Query(None, description="Filter by platform tag"),
    category: Optional[UUID] = Query(None, description="Filter by category ID"),
    status: Optional[PromptStatus] = Query(None, description="Filter by status"),
    featured: bool = Query(False, description="Return only featured prompts"),
    sort_by: SortOrder = Query(SortOrder.NEWEST, description="Sort order"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
) -> PaginatedResponse[PromptResponse]:
    """
    Search prompts with full-text search, filters, and sorting.

    Args:
        db: Database session
        q: Search query string (searches title, description, content)
        platform: Filter by platform tag
        category: Filter by category ID
        status: Filter by prompt status
        featured: Return only featured prompts
        sort_by: Sort order (newest, oldest, most_viewed, least_viewed, highest_rated, lowest_rated)
        page: Page number (1-indexed)
        page_size: Number of items per page

    Returns:
        PaginatedResponse: Paginated list of matching prompts
    """
    skip = (page - 1) * page_size
    try:
        prompts, total = SearchService.search_prompts(
            db=db,
            query=q,
            platform_tag=platform,
            category_id=category,
            status_filter=status,
            featured_only=featured,
            sort_by=sort_by,
            skip=skip,
            limit=page_size,
        )
    except ValueError as e:
        # Handle unsupported sort orders (e.g., highest_rated before Phase 4)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    # Convert to response format with category IDs
    prompt_responses = []
    for prompt in prompts:
        prompt_dict = PromptResponse.model_validate(prompt).model_dump()
        prompt_dict["category_ids"] = [cat.id for cat in prompt.categories]
        prompt_responses.append(PromptResponse(**prompt_dict))

    total_pages = (total + page_size - 1) // page_size

    return PaginatedResponse(
        items=prompt_responses,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )

