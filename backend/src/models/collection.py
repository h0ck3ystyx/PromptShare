"""Collection model for featured prompt collections."""

import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from src.database import Base

if TYPE_CHECKING:
    from src.models.prompt import Prompt
    from src.models.user import User


class Collection(Base):
    """Collection database model for curated prompt sets."""

    __tablename__ = "collections"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    created_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    is_featured = Column(Boolean, nullable=False, default=False, index=True)
    display_order = Column(Integer, nullable=False, default=0, index=True)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime, nullable=False, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))

    # Relationships
    created_by = relationship("User", backref="collections")
    prompts = relationship(
        "Prompt",
        secondary="collection_prompts",
        back_populates="collections",
        order_by="CollectionPrompt.display_order",
    )

    def __repr__(self) -> str:
        """String representation of Collection."""
        return f"<Collection(id={self.id}, name={self.name}, is_featured={self.is_featured})>"


class CollectionPrompt(Base):
    """Many-to-many relationship between collections and prompts with ordering."""

    __tablename__ = "collection_prompts"

    collection_id = Column(UUID(as_uuid=True), ForeignKey("collections.id"), primary_key=True)
    prompt_id = Column(UUID(as_uuid=True), ForeignKey("prompts.id"), primary_key=True)
    display_order = Column(Integer, nullable=False, default=0)

    def __repr__(self) -> str:
        """String representation of CollectionPrompt."""
        return f"<CollectionPrompt(collection_id={self.collection_id}, prompt_id={self.prompt_id}, order={self.display_order})>"

