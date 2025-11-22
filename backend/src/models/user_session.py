"""User session model for tracking active sessions."""

import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from src.database import Base

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


class UserSession(Base):
    """User session model for tracking active login sessions."""

    __tablename__ = "user_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    session_token = Column(String(255), unique=True, nullable=False, index=True)
    device_info = Column(Text, nullable=True)  # User agent, IP, etc.
    ip_address = Column(String(45), nullable=True)  # IPv6 compatible
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(UTC))
    last_activity = Column(DateTime, nullable=False, default=lambda: datetime.now(UTC))
    expires_at = Column(DateTime, nullable=False)

    def __repr__(self) -> str:
        """String representation of UserSession."""
        return f"<UserSession(id={self.id}, user_id={self.user_id}, is_active={self.is_active})>"

