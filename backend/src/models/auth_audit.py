"""Authentication audit log model."""

import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Column, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID

from src.database import Base

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


class AuthAuditLog(Base):
    """Authentication audit log for security monitoring."""

    __tablename__ = "auth_audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    event_type = Column(String(50), nullable=False, index=True)  # login_success, login_failed, password_reset, etc.
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    details = Column(Text, nullable=True)  # JSON or additional details
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(UTC), index=True)

    def __repr__(self) -> str:
        """String representation of AuthAuditLog."""
        return f"<AuthAuditLog(id={self.id}, event_type={self.event_type}, user_id={self.user_id})>"

