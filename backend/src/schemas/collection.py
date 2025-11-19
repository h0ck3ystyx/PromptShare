"""Pydantic schemas for collections."""

from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from src.schemas.prompt import PromptResponse


class CollectionBase(BaseModel):
    """Base collection schema."""

    name: str = Field(..., description="Collection name", max_length=255)
    description: Optional[str] = Field(None, description="Collection description")
    is_featured: bool = Field(False, description="Whether this collection is featured")
    display_order: int = Field(0, ge=0, description="Display order for sorting")


class CollectionCreate(CollectionBase):
    """Schema for creating a collection."""

    prompt_ids: List[UUID] = Field(default_factory=list, description="List of prompt IDs to include in the collection")


class CollectionUpdate(BaseModel):
    """Schema for updating a collection."""

    name: Optional[str] = Field(None, description="Collection name", max_length=255)
    description: Optional[str] = Field(None, description="Collection description")
    is_featured: Optional[bool] = Field(None, description="Whether this collection is featured")
    display_order: Optional[int] = Field(None, ge=0, description="Display order for sorting")
    prompt_ids: Optional[List[UUID]] = Field(None, description="List of prompt IDs to include in the collection")


class CollectionResponse(CollectionBase):
    """Schema for collection response."""

    id: UUID
    created_by_id: UUID
    created_at: str
    updated_at: str
    prompts: List[PromptResponse] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class CollectionListResponse(BaseModel):
    """Schema for list of collections."""

    collections: List[CollectionResponse]
    total: int

