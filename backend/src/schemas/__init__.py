"""Pydantic schemas for API."""

from src.schemas.category import (
    CategoryBase,
    CategoryCreate,
    CategoryResponse,
    CategoryUpdate,
)
from src.schemas.comment import (
    CommentBase,
    CommentCreate,
    CommentResponse,
    CommentTreeResponse,
    CommentUpdate,
)
from src.schemas.common import MessageResponse, PaginatedResponse
from src.schemas.prompt import (
    PromptBase,
    PromptCreate,
    PromptDetailResponse,
    PromptResponse,
    PromptUpdate,
)
from src.schemas.rating import (
    PromptRatingSummary,
    RatingBase,
    RatingCreate,
    RatingResponse,
    RatingUpdate,
)
from src.schemas.upvote import PromptUpvoteSummary, UpvoteResponse
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
    # Comment schemas
    "CommentBase",
    "CommentCreate",
    "CommentResponse",
    "CommentTreeResponse",
    "CommentUpdate",
    # Common schemas
    "MessageResponse",
    "PaginatedResponse",
    # Prompt schemas
    "PromptBase",
    "PromptCreate",
    "PromptDetailResponse",
    "PromptResponse",
    "PromptUpdate",
    # Rating schemas
    "PromptRatingSummary",
    "RatingBase",
    "RatingCreate",
    "RatingResponse",
    "RatingUpdate",
    # Upvote schemas
    "PromptUpvoteSummary",
    "UpvoteResponse",
    # User schemas
    "Token",
    "UserBase",
    "UserCreate",
    "UserLogin",
    "UserResponse",
    "UserUpdate",
]

