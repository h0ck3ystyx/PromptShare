"""Prompt Pydantic schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from src.constants import PlatformTag, PromptStatus


class PromptBase(BaseModel):
    """Base prompt schema."""

    title: str = Field(..., min_length=1, max_length=255, description="Prompt title")
    description: str | None = Field(None, description="Prompt description")
    content: str = Field(..., min_length=1, description="The actual prompt content")
    platform_tags: list[PlatformTag] = Field(
        default_factory=list,
        description="Platform tags (github_copilot, o365_copilot, cursor, claude)",
    )
    use_cases: list[str] = Field(
        default_factory=list,
        description="List of use cases for this prompt",
    )
    usage_tips: str | None = Field(None, description="Usage tips and best practices")
    status: PromptStatus = Field(
        default=PromptStatus.DRAFT,
        description="Prompt status (draft, published, archived)",
    )


class PromptCreate(PromptBase):
    """Schema for creating a prompt."""

    category_ids: list[UUID] = Field(
        default_factory=list,
        description="List of category IDs to associate with this prompt",
    )
    is_featured: bool = Field(
        default=False,
        description="Whether this prompt is featured (admin/moderator only)",
    )


class PromptUpdate(BaseModel):
    """Schema for updating a prompt."""

    title: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    content: str | None = Field(None, min_length=1)
    platform_tags: list[PlatformTag] | None = None
    use_cases: list[str] | None = None
    usage_tips: str | None = None
    status: PromptStatus | None = None
    category_ids: list[UUID] | None = None
    is_featured: bool | None = Field(None, description="Whether this prompt is featured (admin/moderator only)")


class PromptResponse(PromptBase):
    """Schema for prompt response."""

    id: UUID
    author_id: UUID
    created_at: datetime
    updated_at: datetime
    view_count: int
    is_featured: bool
    category_ids: list[UUID] = Field(default_factory=list)

    class Config:
        """Pydantic config."""

        from_attributes = True


class PromptDetailResponse(PromptResponse):
    """Schema for detailed prompt response with author information."""

    author_username: str
    author_full_name: str

    class Config:
        """Pydantic config."""

        from_attributes = True


class PromptCopyRequest(BaseModel):
    """Schema for tracking prompt copy events."""

    prompt_id: UUID

