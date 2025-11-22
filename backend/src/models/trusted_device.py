"""Trusted device model for MFA."""

import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Column, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID

from src.database import Base

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


class TrustedDevice(Base):
    """Trusted device model for MFA trusted devices."""

    __tablename__ = "trusted_devices"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    device_name = Column(String(255), nullable=False)  # User-friendly device name
    device_fingerprint = Column(String(255), nullable=False, unique=True, index=True)  # Unique device identifier
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(UTC))
    last_used = Column(DateTime, nullable=False, default=lambda: datetime.now(UTC))

    def __repr__(self) -> str:
        """String representation of TrustedDevice."""
        return f"<TrustedDevice(id={self.id}, user_id={self.user_id}, device_name={self.device_name})>"

