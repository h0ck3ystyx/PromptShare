"""Application constants."""

from enum import Enum


class UserRole(str, Enum):
    """User role enumeration."""

    ADMIN = "admin"
    MODERATOR = "moderator"
    MEMBER = "member"


class PromptStatus(str, Enum):
    """Prompt status enumeration."""

    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class PlatformTag(str, Enum):
    """Platform tag enumeration."""

    GITHUB_COPILOT = "github_copilot"
    O365_COPILOT = "o365_copilot"
    CURSOR = "cursor"
    CLAUDE = "claude"


class NotificationType(str, Enum):
    """Notification type enumeration."""

    NEW_PROMPT = "new_prompt"
    COMMENT = "comment"
    UPDATE = "update"


class AnalyticsEventType(str, Enum):
    """Analytics event type enumeration."""

    VIEW = "view"
    COPY = "copy"
    SEARCH = "search"


class SortOrder(str, Enum):
    """Sort order enumeration for search and listing."""

    NEWEST = "newest"
    OLDEST = "oldest"
    MOST_VIEWED = "most_viewed"
    LEAST_VIEWED = "least_viewed"
    HIGHEST_RATED = "highest_rated"
    LOWEST_RATED = "lowest_rated"

