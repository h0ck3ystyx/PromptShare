"""Session management service."""

import secrets
from datetime import UTC, datetime, timedelta
from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from src.config import settings
from src.models.user_session import UserSession


class SessionService:
    """Service for managing user sessions."""

    @staticmethod
    def generate_session_token() -> str:
        """
        Generate a secure session token.

        Returns:
            str: Secure random session token
        """
        return secrets.token_urlsafe(32)

    @staticmethod
    def create_session(
        db: Session,
        user_id: UUID,
        access_token: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        device_info: Optional[str] = None,
    ) -> UserSession:
        """
        Create a new user session.

        Args:
            db: Database session
            user_id: User ID
            access_token: JWT access token (stored as session token)
            ip_address: Client IP address
            user_agent: User agent string
            device_info: Device information string

        Returns:
            UserSession: Created session
        """
        # Calculate expiry based on token expiry (30 days default for sessions)
        expires_at = datetime.now(UTC) + timedelta(hours=settings.session_expiry_hours)

        session = UserSession(
            user_id=user_id,
            session_token=access_token,  # Store JWT as session token
            device_info=device_info or user_agent,
            ip_address=ip_address,
            is_active=True,
            expires_at=expires_at,
        )
        db.add(session)
        db.commit()
        db.refresh(session)

        return session

    @staticmethod
    def invalidate_session(db: Session, session_token: str) -> bool:
        """
        Invalidate a session by token.

        Args:
            db: Database session
            session_token: Session token to invalidate

        Returns:
            bool: True if session was found and invalidated
        """
        session = db.query(UserSession).filter(
            UserSession.session_token == session_token,
            UserSession.is_active == True,
        ).first()

        if session:
            session.is_active = False
            db.commit()
            return True

        return False

    @staticmethod
    def invalidate_user_sessions(db: Session, user_id: UUID, exclude_token: Optional[str] = None) -> int:
        """
        Invalidate all sessions for a user (except optionally one).

        Args:
            db: Database session
            user_id: User ID
            exclude_token: Optional token to exclude from invalidation

        Returns:
            int: Number of sessions invalidated
        """
        query = db.query(UserSession).filter(
            UserSession.user_id == user_id,
            UserSession.is_active == True,
        )

        if exclude_token:
            query = query.filter(UserSession.session_token != exclude_token)

        count = query.update({"is_active": False})
        db.commit()

        return count

    @staticmethod
    def update_session_activity(db: Session, session_token: str) -> bool:
        """
        Update last activity timestamp for a session.

        Args:
            db: Database session
            session_token: Session token

        Returns:
            bool: True if session was found and updated
        """
        session = db.query(UserSession).filter(
            UserSession.session_token == session_token,
            UserSession.is_active == True,
        ).first()

        if session:
            session.last_activity = datetime.now(UTC)
            db.commit()
            return True

        return False

    @staticmethod
    def cleanup_expired_sessions(db: Session) -> int:
        """
        Clean up expired sessions.

        Args:
            db: Database session

        Returns:
            int: Number of sessions cleaned up
        """
        now = datetime.now(UTC)
        count = db.query(UserSession).filter(
            UserSession.expires_at < now,
            UserSession.is_active == True,
        ).update({"is_active": False})
        db.commit()

        return count

    @staticmethod
    def get_user_sessions(
        db: Session,
        user_id: UUID,
        active_only: bool = True,
    ) -> list[UserSession]:
        """
        Get all sessions for a user.

        Args:
            db: Database session
            user_id: User ID
            active_only: If True, only return active sessions

        Returns:
            list[UserSession]: List of sessions
        """
        query = db.query(UserSession).filter(UserSession.user_id == user_id)

        if active_only:
            query = query.filter(
                UserSession.is_active == True,
                UserSession.expires_at > datetime.now(UTC),
            )

        return query.order_by(UserSession.last_activity.desc()).all()

