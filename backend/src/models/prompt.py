"""Prompt model."""

import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import relationship

from src.database import Base
from src.models.constants import PlatformTag, PromptStatus

if TYPE_CHECKING:
    from src.models.user import User
    from src.models.category import Category


class Prompt(Base):
    """Prompt database model."""

    __tablename__ = "prompts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    content = Column(Text, nullable=False)
    platform_tags = Column(ARRAY(Enum(PlatformTag)), nullable=False, default=[])
    use_cases = Column(ARRAY(Text), nullable=True, default=[])
    usage_tips = Column(Text, nullable=True)
    author_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime, nullable=False, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))
    view_count = Column(Integer, nullable=False, default=0)
    is_featured = Column(Boolean, nullable=False, default=False)
    status = Column(Enum(PromptStatus), nullable=False, default=PromptStatus.DRAFT)

    # Relationships
    author = relationship("User", backref="prompts")
    categories = relationship(
        "Category",
        secondary="prompt_categories",
        back_populates="prompts",
    )
    collections = relationship(
        "Collection",
        secondary="collection_prompts",
        back_populates="prompts",
    )

    def __repr__(self) -> str:
        """String representation of Prompt."""
        return f"<Prompt(id={self.id}, title={self.title}, status={self.status})>"


class PromptCategory(Base):
    """Many-to-many relationship between prompts and categories."""

    __tablename__ = "prompt_categories"

    prompt_id = Column(UUID(as_uuid=True), ForeignKey("prompts.id"), primary_key=True)
    category_id = Column(UUID(as_uuid=True), ForeignKey("categories.id"), primary_key=True)

