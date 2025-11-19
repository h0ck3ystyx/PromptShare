"""Pydantic schemas for FAQs."""

from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class FAQBase(BaseModel):
    """Base FAQ schema."""

    question: str = Field(..., description="FAQ question", max_length=500)
    answer: str = Field(..., description="FAQ answer")
    category: Optional[str] = Field(None, description="FAQ category (e.g., 'getting_started', 'prompts', 'account')", max_length=100)
    display_order: int = Field(0, ge=0, description="Display order for sorting")
    is_active: bool = Field(True, description="Whether this FAQ is active")


class FAQCreate(FAQBase):
    """Schema for creating an FAQ."""

    pass


class FAQUpdate(BaseModel):
    """Schema for updating an FAQ."""

    question: Optional[str] = Field(None, description="FAQ question", max_length=500)
    answer: Optional[str] = Field(None, description="FAQ answer")
    category: Optional[str] = Field(None, description="FAQ category", max_length=100)
    display_order: Optional[int] = Field(None, ge=0, description="Display order for sorting")
    is_active: Optional[bool] = Field(None, description="Whether this FAQ is active")


class FAQResponse(FAQBase):
    """Schema for FAQ response."""

    id: UUID
    created_by_id: Optional[UUID]
    created_at: str
    updated_at: str

    model_config = ConfigDict(from_attributes=True)


class FAQListResponse(BaseModel):
    """Schema for list of FAQs."""

    faqs: list[FAQResponse]
    total: int

