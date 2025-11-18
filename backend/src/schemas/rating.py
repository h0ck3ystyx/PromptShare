"""Rating Pydantic schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class RatingBase(BaseModel):
    """Base rating schema."""

    rating: int = Field(..., ge=1, le=5, description="Rating value (1-5 stars)")


class RatingCreate(RatingBase):
    """Schema for creating a rating."""

    pass


class RatingUpdate(RatingBase):
    """Schema for updating a rating."""

    pass


class RatingResponse(RatingBase):
    """Schema for rating response."""

    id: UUID
    prompt_id: UUID
    user_id: UUID
    created_at: datetime
    author_username: str

    model_config = ConfigDict(from_attributes=True)


class PromptRatingSummary(BaseModel):
    """Schema for prompt rating summary."""

    prompt_id: UUID
    average_rating: float = Field(..., ge=0.0, le=5.0, description="Average rating")
    total_ratings: int = Field(..., ge=0, description="Total number of ratings")
    rating_distribution: dict[int, int] = Field(
        default_factory=dict,
        description="Distribution of ratings (1-5)",
    )

    model_config = ConfigDict(from_attributes=True)

