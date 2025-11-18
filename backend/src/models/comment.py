"""Comment model."""

import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from src.database import Base

if TYPE_CHECKING:
    from src.models.prompt import Prompt
    from src.models.user import User


class Comment(Base):
    """Comment database model with support for nested comments."""

    __tablename__ = "comments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    prompt_id = Column(UUID(as_uuid=True), ForeignKey("prompts.id"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    content = Column(Text, nullable=False)
    parent_comment_id = Column(
        UUID(as_uuid=True),
        ForeignKey("comments.id"),
        nullable=True,
        index=True,
    )
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime, nullable=False, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))
    is_deleted = Column(Boolean, nullable=False, default=False)  # Soft delete flag

    # Relationships
    prompt = relationship("Prompt", backref="comments")
    user = relationship("User", backref="comments")
    parent_comment = relationship(
        "Comment",
        remote_side=[id],
        backref="replies",
        foreign_keys=[parent_comment_id],
    )

    def __repr__(self) -> str:
        """String representation of Comment."""
        return f"<Comment(id={self.id}, prompt_id={self.prompt_id}, user_id={self.user_id})>"

