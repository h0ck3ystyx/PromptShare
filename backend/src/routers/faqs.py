"""FAQ router endpoints."""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from src.dependencies import AdminDep, CurrentUserDep, DatabaseDep, ModeratorDep, OptionalUserDep
from src.schemas.common import MessageResponse
from src.schemas.faq import FAQCreate, FAQListResponse, FAQResponse, FAQUpdate
from src.services.faq_service import FAQService

router = APIRouter(prefix="/faqs", tags=["faqs"])


@router.post(
    "",
    response_model=FAQResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new FAQ",
)
async def create_faq(
    faq_data: FAQCreate,
    db: DatabaseDep,
    current_user: CurrentUserDep,
) -> FAQResponse:
    """
    Create a new FAQ.

    Args:
        faq_data: FAQ creation data
        db: Database session
        current_user: Authenticated user

    Returns:
        FAQResponse: Created FAQ
    """
    faq = FAQService.create_faq(
        db=db,
        faq_data=faq_data,
        created_by_id=current_user.id,
    )
    return FAQResponse.model_validate(faq)


@router.get(
    "",
    response_model=FAQListResponse,
    summary="List FAQs",
)
async def list_faqs(
    db: DatabaseDep,
    category: Optional[str] = Query(None, description="Filter by FAQ category"),
    active_only: bool = Query(True, description="Return only active FAQs"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
) -> FAQListResponse:
    """
    Get a paginated list of FAQs.

    Args:
        db: Database session
        category: Filter by FAQ category
        active_only: Return only active FAQs
        page: Page number (1-indexed)
        page_size: Number of items per page

    Returns:
        FAQListResponse: Paginated list of FAQs
    """
    skip = (page - 1) * page_size
    faqs, total = FAQService.get_faqs(
        db=db,
        category=category,
        active_only=active_only,
        skip=skip,
        limit=page_size,
    )
    return FAQListResponse(
        faqs=[FAQResponse.model_validate(f) for f in faqs],
        total=total,
    )


@router.get(
    "/{faq_id}",
    response_model=FAQResponse,
    summary="Get FAQ by ID",
)
async def get_faq(
    faq_id: UUID,
    db: DatabaseDep,
) -> FAQResponse:
    """
    Get an FAQ by ID.

    Args:
        faq_id: FAQ ID
        db: Database session

    Returns:
        FAQResponse: FAQ details

    Raises:
        HTTPException: If FAQ not found
    """
    faq = FAQService.get_faq_by_id(db, faq_id)
    if not faq:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="FAQ not found",
        )
    return FAQResponse.model_validate(faq)


@router.put(
    "/{faq_id}",
    response_model=FAQResponse,
    summary="Update an FAQ",
)
async def update_faq(
    faq_id: UUID,
    faq_data: FAQUpdate,
    db: DatabaseDep,
    current_user: CurrentUserDep,
) -> FAQResponse:
    """
    Update an FAQ.

    Args:
        faq_id: FAQ ID
        faq_data: FAQ update data
        db: Database session
        current_user: Authenticated user

    Returns:
        FAQResponse: Updated FAQ

    Raises:
        HTTPException: If FAQ not found or permission denied
    """
    faq = FAQService.update_faq(
        db=db,
        faq_id=faq_id,
        faq_data=faq_data,
        user_id=current_user.id,
    )
    return FAQResponse.model_validate(faq)


@router.delete(
    "/{faq_id}",
    response_model=MessageResponse,
    summary="Delete an FAQ",
)
async def delete_faq(
    faq_id: UUID,
    db: DatabaseDep,
    current_user: CurrentUserDep,
) -> MessageResponse:
    """
    Delete an FAQ.

    Args:
        faq_id: FAQ ID
        db: Database session
        current_user: Authenticated user

    Returns:
        MessageResponse: Success message

    Raises:
        HTTPException: If FAQ not found or permission denied
    """
    FAQService.delete_faq(
        db=db,
        faq_id=faq_id,
        user_id=current_user.id,
    )
    return MessageResponse(message="FAQ deleted successfully")

