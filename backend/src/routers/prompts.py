"""Prompt router endpoints."""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from src.constants import AnalyticsEventType, PlatformTag, PromptStatus, SortOrder
from src.dependencies import CurrentUserDep, DatabaseDep, OptionalUserDep
from src.schemas.common import MessageResponse, PaginatedResponse
from src.schemas.prompt import (
    PromptCreate,
    PromptDetailResponse,
    PromptResponse,
    PromptUpdate,
)
from src.services.analytics_service import AnalyticsService
from src.services.prompt_service import PromptService

router = APIRouter(prefix="/prompts", tags=["prompts"])


@router.get(
    "",
    response_model=PaginatedResponse[PromptResponse],
    summary="List prompts with filters and pagination",
)
async def list_prompts(
    db: DatabaseDep,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    status_filter: Optional[PromptStatus] = Query(None, description="Filter by status"),
    platform_tag: Optional[PlatformTag] = Query(None, description="Filter by platform tag"),
    category_id: Optional[UUID] = Query(None, description="Filter by category ID"),
    author_id: Optional[UUID] = Query(None, description="Filter by author ID"),
    featured_only: bool = Query(False, description="Return only featured prompts"),
    q: Optional[str] = Query(None, description="Keyword search across title, description, and content"),
    title: Optional[str] = Query(None, description="Search in title field"),
    content: Optional[str] = Query(None, description="Search in content field"),
    sort_by: SortOrder = Query(SortOrder.NEWEST, description="Sort order"),
    current_user: OptionalUserDep = None,
) -> PaginatedResponse[PromptResponse]:
    """
    Get a paginated list of prompts with optional filters.

    Args:
        db: Database session
        page: Page number (1-indexed)
        page_size: Number of items per page
        status_filter: Filter by prompt status
        platform_tag: Filter by platform tag
        category_id: Filter by category ID
        author_id: Filter by author ID
        featured_only: Return only featured prompts
        q: Keyword search across title, description, and content
        title: Search in title field
        content: Search in content field
        sort_by: Sort order (newest, oldest, most_viewed, least_viewed, highest_rated, lowest_rated)

    Returns:
        PaginatedResponse: Paginated list of prompts
    """
    skip = (page - 1) * page_size
    try:
        prompts, total = PromptService.get_prompts(
            db=db,
            skip=skip,
            limit=page_size,
            status_filter=status_filter,
            platform_tag=platform_tag.value if platform_tag else None,
            category_id=category_id,
            author_id=author_id,
            featured_only=featured_only,
            search_query=q,
            title_search=title,
            content_search=content,
            sort_by=sort_by,
        )
    except ValueError as e:
        # Handle unsupported sort orders (e.g., highest_rated before Phase 4)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    # Track search event for analytics if search parameters are used
    # This ensures search analytics are captured even when using /api/prompts
    has_search_params = q or title or content
    if has_search_params:
        AnalyticsService.track_event(
            db=db,
            event_type=AnalyticsEventType.SEARCH,
            prompt_id=None,
            user_id=current_user.id if current_user else None,
            metadata={
                "query": q,
                "title": title,
                "content": content,
                "platform_tag": platform_tag.value if platform_tag else None,
                "category_id": str(category_id) if category_id else None,
                "status": status_filter.value if status_filter else None,
                "featured": featured_only,
                "sort_by": sort_by.value,
                "endpoint": "/api/prompts",  # Track which endpoint was used
            },
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


@router.get(
    "/{prompt_id}",
    response_model=PromptDetailResponse,
    summary="Get prompt details by ID",
)
async def get_prompt(
    prompt_id: UUID,
    db: DatabaseDep,
    increment_view: bool = Query(True, description="Increment view count"),
    current_user: OptionalUserDep = None,
) -> PromptDetailResponse:
    """
    Get detailed information about a specific prompt.

    Args:
        prompt_id: Prompt UUID
        db: Database session
        increment_view: Whether to increment the view count

    Returns:
        PromptDetailResponse: Detailed prompt information with author info

    Raises:
        HTTPException: If prompt not found
    """
    prompt = PromptService.get_prompt_by_id(
        db=db,
        prompt_id=prompt_id,
        increment_view=increment_view,
    )

    if not prompt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prompt not found",
        )

    # Track view event for analytics (best-effort, don't fail on errors)
    if increment_view:
        AnalyticsService.track_event(
            db=db,
            event_type=AnalyticsEventType.VIEW,
            prompt_id=prompt_id,
            user_id=current_user.id if current_user else None,
        )

    # Build response with author info and category IDs
    # First create base PromptResponse, then add author fields
    base_dict = PromptResponse.model_validate(prompt).model_dump()
    base_dict["category_ids"] = [cat.id for cat in prompt.categories]
    base_dict["author_username"] = prompt.author.username
    base_dict["author_full_name"] = prompt.author.full_name

    return PromptDetailResponse(**base_dict)


@router.post(
    "",
    response_model=PromptResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new prompt",
)
async def create_prompt(
    prompt_data: PromptCreate,
    db: DatabaseDep,
    current_user: CurrentUserDep,
) -> PromptResponse:
    """
    Create a new prompt.

    Args:
        prompt_data: Prompt creation data
        db: Database session
        current_user: Current authenticated user

    Returns:
        PromptResponse: Created prompt

    Raises:
        HTTPException: If validation fails or categories not found
    """
    prompt = PromptService.create_prompt(
        db=db,
        prompt_data=prompt_data,
        author_id=current_user.id,
        author=current_user,
    )

    # Build response with category IDs
    response_dict = PromptResponse.model_validate(prompt).model_dump()
    response_dict["category_ids"] = [cat.id for cat in prompt.categories]

    return PromptResponse(**response_dict)


@router.put(
    "/{prompt_id}",
    response_model=PromptResponse,
    summary="Update an existing prompt",
)
async def update_prompt(
    prompt_id: UUID,
    prompt_data: PromptUpdate,
    db: DatabaseDep,
    current_user: CurrentUserDep,
) -> PromptResponse:
    """
    Update an existing prompt (author or admin only).

    Args:
        prompt_id: Prompt UUID
        prompt_data: Prompt update data
        db: Database session
        current_user: Current authenticated user

    Returns:
        PromptResponse: Updated prompt

    Raises:
        HTTPException: If prompt not found or user lacks permission
    """
    prompt = PromptService.update_prompt(
        db=db,
        prompt_id=prompt_id,
        prompt_data=prompt_data,
        user=current_user,
    )

    # Build response with category IDs
    response_dict = PromptResponse.model_validate(prompt).model_dump()
    response_dict["category_ids"] = [cat.id for cat in prompt.categories]

    return PromptResponse(**response_dict)


@router.delete(
    "/{prompt_id}",
    response_model=MessageResponse,
    summary="Delete a prompt",
)
async def delete_prompt(
    prompt_id: UUID,
    db: DatabaseDep,
    current_user: CurrentUserDep,
) -> MessageResponse:
    """
    Delete a prompt (author or admin only).

    Args:
        prompt_id: Prompt UUID
        db: Database session
        current_user: Current authenticated user

    Returns:
        MessageResponse: Success message

    Raises:
        HTTPException: If prompt not found or user lacks permission
    """
    PromptService.delete_prompt(
        db=db,
        prompt_id=prompt_id,
        user=current_user,
    )

    return MessageResponse(message="Prompt deleted successfully")


@router.post(
    "/{prompt_id}/copy",
    response_model=MessageResponse,
    summary="Track prompt copy event",
)
async def track_prompt_copy(
    prompt_id: UUID,
    request: Request,
    db: DatabaseDep,
    current_user: OptionalUserDep,
    platform_tag: Optional[str] = Query(None, description="Platform tag context"),
) -> MessageResponse:
    """
    Track a prompt copy event for analytics.
    
    Note: This endpoint is public (no authentication required) to allow
    tracking of copy events from unauthenticated users.

    Args:
        prompt_id: Prompt UUID
        request: FastAPI request object (for IP and user-agent)
        db: Database session
        current_user: Optional authenticated user
        platform_tag: Optional platform tag context

    Returns:
        MessageResponse: Success message

    Raises:
        HTTPException: If prompt not found
    """
    # Extract IP address from request
    # Check for forwarded IP first (behind proxy/load balancer)
    ip_address = request.headers.get("X-Forwarded-For")
    if ip_address:
        # X-Forwarded-For can contain multiple IPs, take the first one
        ip_address = ip_address.split(",")[0].strip()
    else:
        # Fall back to direct client IP
        ip_address = request.client.host if request.client else None
    
    # Extract user-agent from request headers
    user_agent = request.headers.get("User-Agent")
    
    # Track copy event with all available metadata
    PromptService.track_copy(
        db=db,
        prompt_id=prompt_id,
        user_id=current_user.id if current_user else None,
        platform_tag=platform_tag,
        ip_address=ip_address,
        user_agent=user_agent,
    )

    # Also track copy event in analytics_events for consistency (best-effort)
    AnalyticsService.track_event(
        db=db,
        event_type=AnalyticsEventType.COPY,
        prompt_id=prompt_id,
        user_id=current_user.id if current_user else None,
        metadata={
            "platform_tag": platform_tag,
            "ip_address": ip_address,
            "user_agent": user_agent,
        } if platform_tag or ip_address or user_agent else None,
    )

    return MessageResponse(message="Copy event tracked successfully")

