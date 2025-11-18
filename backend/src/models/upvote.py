"""Upvote model."""

import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Column, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from src.database import Base

if TYPE_CHECKING:
    from src.models.prompt import Prompt
    from src.models.user import User


class Upvote(Base):
    """Upvote database model for prompt upvotes."""

    __tablename__ = "upvotes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    prompt_id = Column(UUID(as_uuid=True), ForeignKey("prompts.id"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(UTC))

    # Relationships
    prompt = relationship("Prompt", backref="upvotes")
    user = relationship("User", backref="upvotes")

    # Unique constraint: one upvote per user per prompt
    __table_args__ = (UniqueConstraint("prompt_id", "user_id", name="uq_upvote_prompt_user"),)

    def __repr__(self) -> str:
        """String representation of Upvote."""
        return f"<Upvote(id={self.id}, prompt_id={self.prompt_id}, user_id={self.user_id})>"

