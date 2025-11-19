"""Notification model."""

import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Column, DateTime, Enum, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from src.database import Base
from src.models.constants import NotificationType

if TYPE_CHECKING:
    from src.models.prompt import Prompt
    from src.models.user import User


class Notification(Base):
    """Notification database model."""

    __tablename__ = "notifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    type = Column(Enum(NotificationType), nullable=False, index=True)
    prompt_id = Column(UUID(as_uuid=True), ForeignKey("prompts.id"), nullable=True, index=True)
    message = Column(Text, nullable=False)
    is_read = Column(Boolean, nullable=False, default=False, index=True)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), index=True)

    # Relationships
    user = relationship("User", backref="notifications")
    prompt = relationship("Prompt", backref="notifications")

    def __repr__(self) -> str:
        """String representation of Notification."""
        return f"<Notification(id={self.id}, user_id={self.user_id}, type={self.type}, is_read={self.is_read})>"

