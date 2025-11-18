"""Dependency injection for FastAPI routes."""

from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, Header, status
from fastapi.security import OAuth2PasswordBearer
from typing import Optional
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from src.config import settings
from src.database import get_db
from src.models.user import User

# OAuth2 scheme for token extraction
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

# Type alias for database dependency
DatabaseDep = Annotated[Session, Depends(get_db)]


def get_current_user(
    db: DatabaseDep,
    token: Annotated[str, Depends(oauth2_scheme)],
) -> User:
    """
    Get current authenticated user from JWT token.

    Args:
        db: Database session
        token: JWT token extracted from Authorization header

    Returns:
        User: Current authenticated user

    Raises:
        HTTPException: If token is invalid or user not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        user_id_str: str = payload.get("sub")
        if user_id_str is None:
            raise credentials_exception
        user_id = UUID(user_id_str)
    except (JWTError, ValueError):
        raise credentials_exception

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )

    return user


# Type alias for current user dependency
CurrentUserDep = Annotated[User, Depends(get_current_user)]


def get_optional_user(
    db: DatabaseDep,
    authorization: Optional[str] = Header(None),
) -> User | None:
    """
    Get current user from JWT token if available, otherwise return None.
    
    This allows endpoints to work with or without authentication.

    Args:
        db: Database session
        authorization: Optional Authorization header

    Returns:
        User | None: Current authenticated user or None if not authenticated
    """
    if authorization is None or not authorization.startswith("Bearer "):
        return None
    
    token = authorization.replace("Bearer ", "")
    
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        user_id_str: str = payload.get("sub")
        if user_id_str is None:
            return None
        user_id = UUID(user_id_str)
    except (JWTError, ValueError):
        return None

    user = db.query(User).filter(User.id == user_id).first()
    if user is None or not user.is_active:
        return None

    return user


# Type alias for optional user dependency
OptionalUserDep = Annotated[User | None, Depends(get_optional_user)]


def require_admin(current_user: CurrentUserDep) -> User:
    """
    Require admin role for endpoint access.

    Args:
        current_user: Current authenticated user

    Returns:
        User: Current user if admin

    Raises:
        HTTPException: If user is not an admin
    """
    from src.constants import UserRole

    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user


def require_moderator(current_user: CurrentUserDep) -> User:
    """
    Require moderator role for endpoint access.

    Args:
        current_user: Current authenticated user

    Returns:
        User: Current user if moderator

    Raises:
        HTTPException: If user is not a moderator
    """
    from src.constants import UserRole

    if current_user.role != UserRole.MODERATOR:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Moderator access required",
        )
    return current_user


def require_admin_or_moderator(current_user: CurrentUserDep) -> User:
    """
    Require admin or moderator role for endpoint access.

    Args:
        current_user: Current authenticated user

    Returns:
        User: Current user if admin or moderator

    Raises:
        HTTPException: If user is not an admin or moderator
    """
    from src.constants import UserRole

    if current_user.role not in (UserRole.ADMIN, UserRole.MODERATOR):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin or moderator access required",
        )
    return current_user


# Type aliases for permission dependencies
AdminDep = Annotated[User, Depends(require_admin)]
ModeratorDep = Annotated[User, Depends(require_moderator)]
AdminOrModeratorDep = Annotated[User, Depends(require_admin_or_moderator)]

