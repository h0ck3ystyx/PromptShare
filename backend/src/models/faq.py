"""FAQ model for help and frequently asked questions."""

import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from src.database import Base

if TYPE_CHECKING:
    from src.models.user import User


class FAQ(Base):
    """FAQ database model for help and frequently asked questions."""

    __tablename__ = "faqs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    question = Column(String(500), nullable=False, index=True)
    answer = Column(Text, nullable=False)
    category = Column(String(100), nullable=True, index=True)  # e.g., "getting_started", "prompts", "account"
    display_order = Column(Integer, nullable=False, default=0, index=True)
    is_active = Column(Boolean, nullable=False, default=True, index=True)
    created_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime, nullable=False, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))

    # Relationships
    created_by = relationship("User", backref="faqs")

    def __repr__(self) -> str:
        """String representation of FAQ."""
        return f"<FAQ(id={self.id}, question={self.question[:50]}..., category={self.category})>"

