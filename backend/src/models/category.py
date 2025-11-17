"""Category model."""

import uuid
from sqlalchemy import Column, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from src.database import Base


class Category(Base):
    """Category database model."""

    __tablename__ = "categories"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    slug = Column(String(100), unique=True, nullable=False, index=True)

    # Relationships
    prompts = relationship(
        "Prompt",
        secondary="prompt_categories",
        back_populates="categories",
    )

    def __repr__(self) -> str:
        """String representation of Category."""
        return f"<Category(id={self.id}, name={self.name}, slug={self.slug})>"

