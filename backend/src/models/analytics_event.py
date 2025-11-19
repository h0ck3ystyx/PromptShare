"""Analytics event model for tracking usage and engagement."""

import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Index, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from src.database import Base
from src.constants import AnalyticsEventType

if TYPE_CHECKING:
    from src.models.prompt import Prompt
    from src.models.user import User


class AnalyticsEvent(Base):
    """Analytics event database model for tracking usage and engagement."""

    __tablename__ = "analytics_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_type = Column(Enum(AnalyticsEventType), nullable=False, index=True)
    prompt_id = Column(UUID(as_uuid=True), ForeignKey("prompts.id"), nullable=True, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True)
    event_metadata = Column(JSONB, nullable=True)  # Flexible JSON for additional event data
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), index=True)

    # Relationships
    prompt = relationship("Prompt", backref="analytics_events")
    user = relationship("User", backref="analytics_events")

    # Composite index for common queries
    __table_args__ = (
        Index("ix_analytics_events_type_created", "event_type", "created_at"),
        Index("ix_analytics_events_prompt_type", "prompt_id", "event_type"),
    )

    def __repr__(self) -> str:
        """String representation of AnalyticsEvent."""
        return f"<AnalyticsEvent(id={self.id}, event_type={self.event_type}, prompt_id={self.prompt_id}, created_at={self.created_at})>"

