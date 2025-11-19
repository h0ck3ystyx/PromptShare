"""Collection service for managing prompt collections."""

from typing import List, Optional
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from src.constants import PromptStatus, UserRole
from src.models.collection import Collection, CollectionPrompt
from src.models.prompt import Prompt
from src.models.user import User
from src.schemas.collection import CollectionCreate, CollectionUpdate


class CollectionService:
    """Service for handling collection operations."""

    @staticmethod
    def create_collection(
        db: Session,
        collection_data: CollectionCreate,
        created_by_id: UUID,
    ) -> Collection:
        """
        Create a new collection.

        Args:
            db: Database session
            collection_data: Collection creation data
            created_by_id: ID of the user creating the collection

        Returns:
            Collection: Created collection object

        Raises:
            HTTPException: If prompts not found or other validation errors
        """
        # Verify user exists
        user = db.query(User).filter(User.id == created_by_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        # Check permission for is_featured
        if collection_data.is_featured and user.role not in (UserRole.ADMIN, UserRole.MODERATOR):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admins and moderators can create featured collections",
            )

        # Validate prompts if provided and preserve order
        prompt_map = {}
        if collection_data.prompt_ids:
            # Query all prompts at once
            all_prompts = (
                db.query(Prompt)
                .filter(
                    Prompt.id.in_(collection_data.prompt_ids),
                    Prompt.status == PromptStatus.PUBLISHED,  # Only include published prompts
                )
                .all()
            )
            # Build a map for quick lookup
            prompt_map = {p.id: p for p in all_prompts}
            
            # Check if all prompts were found
            if len(prompt_map) != len(collection_data.prompt_ids):
                found_ids = set(prompt_map.keys())
                missing_ids = set(collection_data.prompt_ids) - found_ids
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Prompts not found or not published: {list(missing_ids)}",
                )

        # Create collection
        collection = Collection(
            name=collection_data.name,
            description=collection_data.description,
            is_featured=collection_data.is_featured,
            display_order=collection_data.display_order,
            created_by_id=created_by_id,
        )

        db.add(collection)
        db.flush()  # Get collection.id

        # Associate prompts with display order - preserve client's order
        for idx, prompt_id in enumerate(collection_data.prompt_ids):
            prompt = prompt_map[prompt_id]
            collection_prompt = CollectionPrompt(
                collection_id=collection.id,
                prompt_id=prompt.id,
                display_order=idx,
            )
            db.add(collection_prompt)

        db.commit()
        db.refresh(collection)
        return collection

    @staticmethod
    def get_collection_by_id(db: Session, collection_id: UUID) -> Optional[Collection]:
        """
        Get a collection by ID.

        Args:
            db: Database session
            collection_id: Collection ID

        Returns:
            Collection: Collection object or None if not found
        """
        return db.query(Collection).filter(Collection.id == collection_id).first()

    @staticmethod
    def get_collections(
        db: Session,
        featured_only: bool = False,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[List[Collection], int]:
        """
        Get collections with optional filters.

        Args:
            db: Database session
            featured_only: Return only featured collections
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            tuple: (list of collections, total count)
        """
        query = db.query(Collection)

        if featured_only:
            query = query.filter(Collection.is_featured == True)

        total = query.count()
        collections = (
            query.order_by(Collection.display_order, Collection.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

        return collections, total

    @staticmethod
    def update_collection(
        db: Session,
        collection_id: UUID,
        collection_data: CollectionUpdate,
        user_id: UUID,
    ) -> Collection:
        """
        Update a collection.

        Args:
            db: Database session
            collection_id: Collection ID
            collection_data: Collection update data
            user_id: ID of the user updating the collection

        Returns:
            Collection: Updated collection object

        Raises:
            HTTPException: If collection not found or permission denied
        """
        collection = CollectionService.get_collection_by_id(db, collection_id)
        if not collection:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Collection not found",
            )

        # Check permissions: creator or admin/moderator
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        if collection.created_by_id != user_id and user.role not in (UserRole.ADMIN, UserRole.MODERATOR):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the creator or admins/moderators can update collections",
            )

        # Check permission for is_featured
        if collection_data.is_featured is not None and collection_data.is_featured and user.role not in (UserRole.ADMIN, UserRole.MODERATOR):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admins and moderators can set featured status",
            )

        # Update fields
        if collection_data.name is not None:
            collection.name = collection_data.name
        if collection_data.description is not None:
            collection.description = collection_data.description
        if collection_data.is_featured is not None:
            collection.is_featured = collection_data.is_featured
        if collection_data.display_order is not None:
            collection.display_order = collection_data.display_order

        # Update prompts if provided - preserve client's order
        if collection_data.prompt_ids is not None:
            # Remove existing associations
            db.query(CollectionPrompt).filter(CollectionPrompt.collection_id == collection_id).delete()

            # Validate and add new prompts - preserve order
            if collection_data.prompt_ids:
                # Query all prompts at once
                all_prompts = (
                    db.query(Prompt)
                    .filter(
                        Prompt.id.in_(collection_data.prompt_ids),
                        Prompt.status == PromptStatus.PUBLISHED,
                    )
                    .all()
                )
                # Build a map for quick lookup
                prompt_map = {p.id: p for p in all_prompts}
                
                if len(prompt_map) != len(collection_data.prompt_ids):
                    found_ids = set(prompt_map.keys())
                    missing_ids = set(collection_data.prompt_ids) - found_ids
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Prompts not found or not published: {list(missing_ids)}",
                    )

                # Add new associations - preserve client's order
                for idx, prompt_id in enumerate(collection_data.prompt_ids):
                    prompt = prompt_map[prompt_id]
                    collection_prompt = CollectionPrompt(
                        collection_id=collection.id,
                        prompt_id=prompt.id,
                        display_order=idx,
                    )
                    db.add(collection_prompt)

        db.commit()
        db.refresh(collection)
        return collection

    @staticmethod
    def delete_collection(db: Session, collection_id: UUID, user_id: UUID) -> None:
        """
        Delete a collection.

        Args:
            db: Database session
            collection_id: Collection ID
            user_id: ID of the user deleting the collection

        Raises:
            HTTPException: If collection not found or permission denied
        """
        collection = CollectionService.get_collection_by_id(db, collection_id)
        if not collection:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Collection not found",
            )

        # Check permissions: creator or admin/moderator
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        if collection.created_by_id != user_id and user.role not in (UserRole.ADMIN, UserRole.MODERATOR):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the creator or admins/moderators can delete collections",
            )

        # Delete collection (cascade will handle collection_prompts)
        db.delete(collection)
        db.commit()

