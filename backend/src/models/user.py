"""User model."""

import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Column, DateTime, Enum, String, Text
from sqlalchemy.dialects.postgresql import UUID

from src.database import Base
from src.models.constants import UserRole

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


class User(Base):
    """User database model."""

    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    full_name = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), nullable=False, default=UserRole.MEMBER)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(UTC))
    last_login = Column(DateTime, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    
    # Local authentication fields
    password_hash = Column(String(255), nullable=True)  # Nullable to support LDAP users
    email_verified = Column(Boolean, nullable=False, default=False)
    auth_method = Column(String(20), nullable=False, default="ldap")  # 'ldap' or 'local'
    
    # MFA fields
    mfa_enabled = Column(Boolean, nullable=False, default=False)
    mfa_secret = Column(String(255), nullable=True)  # Encrypted MFA secret

    def __repr__(self) -> str:
        """String representation of User."""
        return f"<User(id={self.id}, email={self.email}, username={self.username})>"

