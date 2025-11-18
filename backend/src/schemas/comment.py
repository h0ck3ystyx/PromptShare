"""Comment Pydantic schemas."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class CommentBase(BaseModel):
    """Base comment schema."""

    content: str = Field(..., min_length=1, max_length=5000, description="Comment content")


class CommentCreate(CommentBase):
    """Schema for creating a comment."""

    parent_comment_id: Optional[UUID] = Field(None, description="Parent comment ID for nested comments")


class CommentUpdate(BaseModel):
    """Schema for updating a comment."""

    content: str = Field(..., min_length=1, max_length=5000, description="Updated comment content")


class CommentResponse(CommentBase):
    """Schema for comment response."""

    id: UUID
    prompt_id: UUID
    user_id: UUID
    parent_comment_id: Optional[UUID]
    created_at: datetime
    updated_at: datetime
    is_deleted: bool
    author_username: str
    author_full_name: str
    reply_count: int = Field(default=0, description="Number of replies to this comment")

    model_config = ConfigDict(from_attributes=True)


class CommentTreeResponse(CommentResponse):
    """Schema for comment with nested replies."""

    replies: list["CommentTreeResponse"] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)

