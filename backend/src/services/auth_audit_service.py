"""Authentication audit logging service."""

from datetime import UTC, datetime
from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from src.models.auth_audit import AuthAuditLog


class AuthAuditService:
    """Service for logging authentication events."""

    @staticmethod
    def log_event(
        db: Session,
        event_type: str,
        user_id: Optional[UUID] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        details: Optional[str] = None,
    ) -> AuthAuditLog:
        """
        Log an authentication event.

        Args:
            db: Database session
            event_type: Type of event (e.g., 'login_success', 'login_failed', 'password_reset')
            user_id: User ID (optional, for failed logins)
            ip_address: IP address
            user_agent: User agent string
            details: Additional details (JSON string or plain text)

        Returns:
            AuthAuditLog: Created audit log entry
        """
        audit_log = AuthAuditLog(
            user_id=user_id,
            event_type=event_type,
            ip_address=ip_address,
            user_agent=user_agent,
            details=details,
        )
        db.add(audit_log)
        db.commit()
        db.refresh(audit_log)

        return audit_log

    @staticmethod
    def get_user_audit_logs(
        db: Session,
        user_id: UUID,
        limit: int = 50,
    ) -> list[AuthAuditLog]:
        """
        Get audit logs for a user.

        Args:
            db: Database session
            user_id: User ID
            limit: Maximum number of logs to return

        Returns:
            list[AuthAuditLog]: List of audit log entries
        """
        logs = (
            db.query(AuthAuditLog)
            .filter(AuthAuditLog.user_id == user_id)
            .order_by(AuthAuditLog.created_at.desc())
            .limit(limit)
            .all()
        )

        return logs

