"""User Pydantic schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr

from src.constants import UserRole


class UserBase(BaseModel):
    """Base user schema."""

    email: EmailStr
    username: str
    full_name: str


class UserCreate(UserBase):
    """Schema for creating a user."""

    pass


class UserUpdate(BaseModel):
    """Schema for updating a user."""

    email: EmailStr | None = None
    username: str | None = None
    full_name: str | None = None
    role: UserRole | None = None
    is_active: bool | None = None


class UserResponse(UserBase):
    """Schema for user response."""

    id: UUID
    role: UserRole
    created_at: datetime
    last_login: datetime | None
    is_active: bool

    class Config:
        """Pydantic config."""

        from_attributes = True


class UserLogin(BaseModel):
    """Schema for user login."""

    username: str
    password: str


class Token(BaseModel):
    """Schema for authentication token."""

    access_token: str
    token_type: str = "bearer"

