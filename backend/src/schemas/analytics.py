"""Analytics schemas for API responses."""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class PromptAnalyticsResponse(BaseModel):
    """Response schema for prompt analytics."""

    model_config = ConfigDict(from_attributes=True)

    prompt_id: str
    prompt_title: str
    total_views: int
    total_copies: int
    views_series: Dict[str, int] = Field(default_factory=dict)
    copies_series: Dict[str, int] = Field(default_factory=dict)
    period_days: int


class TopPromptItem(BaseModel):
    """Schema for top prompt item in analytics."""

    prompt_id: str
    title: str
    view_count: Optional[int] = None
    copy_count: Optional[int] = None


class OverviewAnalyticsResponse(BaseModel):
    """Response schema for overview analytics."""

    period_days: int
    total_views: int
    total_copies: int
    total_searches: int
    top_viewed_prompts: List[TopPromptItem]
    top_copied_prompts: List[TopPromptItem]
    daily_activity: Dict[str, Dict[str, int]] = Field(default_factory=dict)

