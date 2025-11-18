"""Category Pydantic schemas."""

from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class CategoryBase(BaseModel):
    """Base category schema."""

    name: str = Field(..., min_length=1, max_length=100, description="Category name")
    description: str | None = Field(None, description="Category description")
    slug: str = Field(..., min_length=1, max_length=100, description="URL-friendly slug")


class CategoryCreate(CategoryBase):
    """Schema for creating a category."""

    pass


class CategoryUpdate(BaseModel):
    """Schema for updating a category."""

    name: str | None = Field(None, min_length=1, max_length=100)
    description: str | None = None
    slug: str | None = Field(None, min_length=1, max_length=100)


class CategoryResponse(CategoryBase):
    """Schema for category response."""

    id: UUID

    model_config = ConfigDict(from_attributes=True)

