"""User follow model for following categories."""

import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import Column, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from src.database import Base

if TYPE_CHECKING:
    from src.models.category import Category
    from src.models.user import User


class UserFollow(Base):
    """User follow database model for following categories."""

    __tablename__ = "user_follows"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    category_id = Column(UUID(as_uuid=True), ForeignKey("categories.id"), nullable=False, index=True)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    # Relationships
    user = relationship("User", backref="follows")
    category = relationship("Category", backref="followers")

    # Unique constraint: user can only follow a category once
    __table_args__ = (UniqueConstraint("user_id", "category_id", name="uq_user_category_follow"),)

    def __repr__(self) -> str:
        """String representation of UserFollow."""
        return f"<UserFollow(id={self.id}, user_id={self.user_id}, category_id={self.category_id})>"

