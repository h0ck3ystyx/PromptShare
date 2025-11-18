"""Upvote Pydantic schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class UpvoteResponse(BaseModel):
    """Schema for upvote response."""

    id: UUID
    prompt_id: UUID
    user_id: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PromptUpvoteSummary(BaseModel):
    """Schema for prompt upvote summary."""

    prompt_id: UUID
    total_upvotes: int = Field(..., ge=0, description="Total number of upvotes")
    user_has_upvoted: bool = Field(default=False, description="Whether current user has upvoted")

    model_config = ConfigDict(from_attributes=True)

