"""Prompt copy event model for analytics."""

import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Column, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from src.database import Base

if TYPE_CHECKING:
    from src.models.prompt import Prompt
    from src.models.user import User


class PromptCopyEvent(Base):
    """Prompt copy event database model for analytics tracking."""

    __tablename__ = "prompt_copy_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    prompt_id = Column(UUID(as_uuid=True), ForeignKey("prompts.id"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True)
    copied_at = Column(DateTime, nullable=False, default=lambda: datetime.now(UTC), index=True)
    platform_tag = Column(String(50), nullable=True)  # Optional platform context
    ip_address = Column(String(45), nullable=True)  # IPv4 or IPv6
    user_agent = Column(String(500), nullable=True)  # Browser/client info

    # Relationships
    prompt = relationship("Prompt", backref="copy_events")
    user = relationship("User", backref="copy_events")

    def __repr__(self) -> str:
        """String representation of PromptCopyEvent."""
        return f"<PromptCopyEvent(id={self.id}, prompt_id={self.prompt_id}, copied_at={self.copied_at})>"

