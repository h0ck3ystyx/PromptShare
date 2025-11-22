"""User Pydantic schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr

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

    model_config = ConfigDict(from_attributes=True)


class UserLogin(BaseModel):
    """Schema for user login."""

    username: str
    password: str


class Token(BaseModel):
    """Schema for authentication token."""

    access_token: str
    token_type: str = "bearer"
    mfa_required: bool = False  # Indicates if MFA verification is required


class UserRoleUpdate(BaseModel):
    """Schema for updating user role."""

    role: UserRole


class UserStatusUpdate(BaseModel):
    """Schema for updating user status."""

    is_active: bool


class UserStats(BaseModel):
    """Schema for user statistics."""

    user_id: UUID
    prompt_count: int
    comment_count: int
    rating_count: int
    upvote_count: int
    total_prompt_views: int

    model_config = ConfigDict(from_attributes=True)

