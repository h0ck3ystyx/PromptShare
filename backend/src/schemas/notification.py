"""Notification Pydantic schemas."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from src.constants import NotificationType


class NotificationResponse(BaseModel):
    """Schema for notification response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    type: NotificationType
    prompt_id: Optional[UUID] = None
    message: str
    is_read: bool
    created_at: datetime


class NotificationListResponse(BaseModel):
    """Schema for list of notifications."""

    notifications: list[NotificationResponse]
    total: int
    unread_count: int


class NotificationUpdateRequest(BaseModel):
    """Schema for updating notification (mark as read)."""

    is_read: bool = True

