"""Pydantic schemas for onboarding materials."""

from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from src.schemas.collection import CollectionResponse
from src.schemas.faq import FAQResponse


class OnboardingSection(BaseModel):
    """Schema for an onboarding section."""

    title: str
    content: str
    order: int


class OnboardingResponse(BaseModel):
    """Schema for onboarding materials response."""

    welcome_message: str
    getting_started: List[OnboardingSection]
    featured_collections: List[CollectionResponse]
    quick_tips: List[str]
    faqs: List[FAQResponse]

    model_config = ConfigDict(from_attributes=True)


class BestPracticesResponse(BaseModel):
    """Schema for best practices response."""

    general_tips: List[str]
    platform_specific_tips: dict[str, List[str]]
    common_mistakes: List[str]
    resources: List[dict[str, str]]

    model_config = ConfigDict(from_attributes=True)

