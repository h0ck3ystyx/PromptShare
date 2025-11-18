"""Rating model."""

import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Column, DateTime, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from src.database import Base

if TYPE_CHECKING:
    from src.models.prompt import Prompt
    from src.models.user import User


class Rating(Base):
    """Rating database model for prompt ratings (1-5 stars)."""

    __tablename__ = "ratings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    prompt_id = Column(UUID(as_uuid=True), ForeignKey("prompts.id"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    rating = Column(Integer, nullable=False)  # 1-5 stars
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(UTC))

    # Relationships
    prompt = relationship("Prompt", backref="ratings")
    user = relationship("User", backref="ratings")

    # Unique constraint: one rating per user per prompt
    __table_args__ = (UniqueConstraint("prompt_id", "user_id", name="uq_rating_prompt_user"),)

    def __repr__(self) -> str:
        """String representation of Rating."""
        return f"<Rating(id={self.id}, prompt_id={self.prompt_id}, user_id={self.user_id}, rating={self.rating})>"

