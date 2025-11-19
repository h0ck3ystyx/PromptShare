"""Collection router endpoints."""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from src.dependencies import AdminDep, AdminOrModeratorDep, CurrentUserDep, DatabaseDep, ModeratorDep
from src.schemas.collection import (
    CollectionCreate,
    CollectionListResponse,
    CollectionResponse,
    CollectionUpdate,
)
from src.schemas.common import MessageResponse
from src.services.collection_service import CollectionService

router = APIRouter(prefix="/collections", tags=["collections"])


@router.post(
    "",
    response_model=CollectionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new collection (Admin/Moderator only)",
)
async def create_collection(
    collection_data: CollectionCreate,
    db: DatabaseDep,
    current_user: AdminOrModeratorDep,  # Only admins/moderators can create collections
) -> CollectionResponse:
    """
    Create a new prompt collection.

    Args:
        collection_data: Collection creation data
        db: Database session
        current_user: Authenticated user

    Returns:
        CollectionResponse: Created collection
    """
    collection = CollectionService.create_collection(
        db=db,
        collection_data=collection_data,
        created_by_id=current_user.id,
    )
    return CollectionResponse.model_validate(collection)


@router.get(
    "",
    response_model=CollectionListResponse,
    summary="List collections",
)
async def list_collections(
    db: DatabaseDep,
    featured_only: bool = Query(False, description="Return only featured collections"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
) -> CollectionListResponse:
    """
    Get a paginated list of collections.

    Args:
        db: Database session
        featured_only: Return only featured collections
        page: Page number (1-indexed)
        page_size: Number of items per page

    Returns:
        CollectionListResponse: Paginated list of collections
    """
    skip = (page - 1) * page_size
    collections, total = CollectionService.get_collections(
        db=db,
        featured_only=featured_only,
        skip=skip,
        limit=page_size,
    )
    return CollectionListResponse(
        collections=[CollectionResponse.model_validate(c) for c in collections],
        total=total,
    )


@router.get(
    "/{collection_id}",
    response_model=CollectionResponse,
    summary="Get collection by ID",
)
async def get_collection(
    collection_id: UUID,
    db: DatabaseDep,
) -> CollectionResponse:
    """
    Get a collection by ID.

    Args:
        collection_id: Collection ID
        db: Database session

    Returns:
        CollectionResponse: Collection details

    Raises:
        HTTPException: If collection not found
    """
    collection = CollectionService.get_collection_by_id(db, collection_id)
    if not collection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Collection not found",
        )
    return CollectionResponse.model_validate(collection)


@router.put(
    "/{collection_id}",
    response_model=CollectionResponse,
    summary="Update a collection (Admin/Moderator only)",
)
async def update_collection(
    collection_id: UUID,
    collection_data: CollectionUpdate,
    db: DatabaseDep,
    current_user: AdminOrModeratorDep,  # Only admins/moderators can update collections
) -> CollectionResponse:
    """
    Update a collection.

    Args:
        collection_id: Collection ID
        collection_data: Collection update data
        db: Database session
        current_user: Authenticated user

    Returns:
        CollectionResponse: Updated collection

    Raises:
        HTTPException: If collection not found or permission denied
    """
    collection = CollectionService.update_collection(
        db=db,
        collection_id=collection_id,
        collection_data=collection_data,
        user_id=current_user.id,
    )
    return CollectionResponse.model_validate(collection)


@router.delete(
    "/{collection_id}",
    response_model=MessageResponse,
    summary="Delete a collection (Admin/Moderator only)",
)
async def delete_collection(
    collection_id: UUID,
    db: DatabaseDep,
    current_user: AdminOrModeratorDep,  # Only admins/moderators can delete collections
) -> MessageResponse:
    """
    Delete a collection.

    Args:
        collection_id: Collection ID
        db: Database session
        current_user: Authenticated user

    Returns:
        MessageResponse: Success message

    Raises:
        HTTPException: If collection not found or permission denied
    """
    CollectionService.delete_collection(
        db=db,
        collection_id=collection_id,
        user_id=current_user.id,
    )
    return MessageResponse(message="Collection deleted successfully")

