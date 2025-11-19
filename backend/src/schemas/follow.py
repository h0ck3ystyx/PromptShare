"""Follow Pydantic schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from src.schemas.category import CategoryResponse


class FollowResponse(BaseModel):
    """Schema for follow response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    category_id: UUID
    created_at: datetime
    category: CategoryResponse


class FollowListResponse(BaseModel):
    """Schema for list of followed categories."""

    categories: list[CategoryResponse]
    total: int


class FollowRequest(BaseModel):
    """Schema for follow request."""

    category_id: UUID

