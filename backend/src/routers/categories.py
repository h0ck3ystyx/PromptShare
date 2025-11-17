"""Category router endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from src.dependencies import CurrentUserDep, DatabaseDep
from src.schemas.category import CategoryCreate, CategoryResponse, CategoryUpdate
from src.schemas.common import MessageResponse, PaginatedResponse
from src.services.category_service import CategoryService

router = APIRouter(prefix="/categories", tags=["categories"])


@router.get(
    "",
    response_model=PaginatedResponse[CategoryResponse],
    summary="List all categories",
)
async def list_categories(
    db: DatabaseDep,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(100, ge=1, le=100, description="Items per page"),
) -> PaginatedResponse[CategoryResponse]:
    """
    Get a paginated list of all categories.

    Args:
        db: Database session
        page: Page number (1-indexed)
        page_size: Number of items per page

    Returns:
        PaginatedResponse: Paginated list of categories
    """
    skip = (page - 1) * page_size
    categories, total = CategoryService.get_categories(
        db=db,
        skip=skip,
        limit=page_size,
    )

    total_pages = (total + page_size - 1) // page_size

    return PaginatedResponse(
        items=[CategoryResponse.model_validate(cat) for cat in categories],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get(
    "/{category_id}",
    response_model=CategoryResponse,
    summary="Get category by ID",
)
async def get_category(
    category_id: UUID,
    db: DatabaseDep,
) -> CategoryResponse:
    """
    Get category information by ID.

    Args:
        category_id: Category UUID
        db: Database session

    Returns:
        CategoryResponse: Category information

    Raises:
        HTTPException: If category not found
    """
    category = CategoryService.get_category_by_id(db=db, category_id=category_id)

    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found",
        )

    return CategoryResponse.model_validate(category)


@router.get(
    "/slug/{slug}",
    response_model=CategoryResponse,
    summary="Get category by slug",
)
async def get_category_by_slug(
    slug: str,
    db: DatabaseDep,
) -> CategoryResponse:
    """
    Get category information by slug.

    Args:
        slug: Category slug
        db: Database session

    Returns:
        CategoryResponse: Category information

    Raises:
        HTTPException: If category not found
    """
    category = CategoryService.get_category_by_slug(db=db, slug=slug)

    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found",
        )

    return CategoryResponse.model_validate(category)


@router.post(
    "",
    response_model=CategoryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new category (admin/moderator only)",
)
async def create_category(
    category_data: CategoryCreate,
    db: DatabaseDep,
    current_user: CurrentUserDep,
) -> CategoryResponse:
    """
    Create a new category (admin or moderator only).

    Args:
        category_data: Category creation data
        db: Database session
        current_user: Current authenticated user

    Returns:
        CategoryResponse: Created category

    Raises:
        HTTPException: If user lacks permission or category already exists
    """
    category = CategoryService.create_category(
        db=db,
        category_data=category_data,
        user=current_user,
    )

    return CategoryResponse.model_validate(category)


@router.put(
    "/{category_id}",
    response_model=CategoryResponse,
    summary="Update an existing category (admin/moderator only)",
)
async def update_category(
    category_id: UUID,
    category_data: CategoryUpdate,
    db: DatabaseDep,
    current_user: CurrentUserDep,
) -> CategoryResponse:
    """
    Update an existing category (admin or moderator only).

    Args:
        category_id: Category UUID
        category_data: Category update data
        db: Database session
        current_user: Current authenticated user

    Returns:
        CategoryResponse: Updated category

    Raises:
        HTTPException: If category not found or user lacks permission
    """
    category = CategoryService.update_category(
        db=db,
        category_id=category_id,
        category_data=category_data,
        user=current_user,
    )

    return CategoryResponse.model_validate(category)


@router.delete(
    "/{category_id}",
    response_model=MessageResponse,
    summary="Delete a category (admin only)",
)
async def delete_category(
    category_id: UUID,
    db: DatabaseDep,
    current_user: CurrentUserDep,
) -> MessageResponse:
    """
    Delete a category (admin only).

    Args:
        category_id: Category UUID
        db: Database session
        current_user: Current authenticated user

    Returns:
        MessageResponse: Success message

    Raises:
        HTTPException: If category not found, user lacks permission, or category is in use
    """
    CategoryService.delete_category(
        db=db,
        category_id=category_id,
        user=current_user,
    )

    return MessageResponse(message="Category deleted successfully")

