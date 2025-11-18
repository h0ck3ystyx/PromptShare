"""Pydantic schemas for API."""

from src.schemas.category import (
    CategoryBase,
    CategoryCreate,
    CategoryResponse,
    CategoryUpdate,
)
from src.schemas.common import MessageResponse, PaginatedResponse
from src.schemas.prompt import (
    PromptBase,
    PromptCreate,
    PromptDetailResponse,
    PromptResponse,
    PromptUpdate,
)
from src.schemas.user import (
    Token,
    UserBase,
    UserCreate,
    UserLogin,
    UserResponse,
    UserUpdate,
)

__all__ = [
    # Category schemas
    "CategoryBase",
    "CategoryCreate",
    "CategoryResponse",
    "CategoryUpdate",
    # Common schemas
    "MessageResponse",
    "PaginatedResponse",
    # Prompt schemas
    "PromptBase",
    "PromptCreate",
    "PromptDetailResponse",
    "PromptResponse",
    "PromptUpdate",
    # User schemas
    "Token",
    "UserBase",
    "UserCreate",
    "UserLogin",
    "UserResponse",
    "UserUpdate",
]

