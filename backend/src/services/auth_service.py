"""Authentication service for LDAP/AD and local authentication."""

import ldap
import secrets
from datetime import UTC, datetime, timedelta
from typing import Optional
from uuid import UUID

from jose import JWTError, jwt
from sqlalchemy.orm import Session

from src.config import settings
from src.models.user import User
from src.constants import UserRole
from src.services.password_service import PasswordService


class AuthService:
    """Service for handling authentication operations."""

    @staticmethod
    def authenticate_ldap(username: str, password: str) -> Optional[dict]:
        """
        Authenticate user against LDAP/Active Directory.

        Args:
            username: Username for authentication
            password: Password for authentication

        Returns:
            dict: User information from LDAP if authentication succeeds, None otherwise
        """
        conn = None
        user_conn = None

        try:
            # Initialize LDAP connection
            conn = ldap.initialize(settings.ldap_server)
            conn.set_option(ldap.OPT_REFERRALS, 0)
            conn.simple_bind_s(settings.ldap_user_dn, settings.ldap_password)

            # Search for user
            search_filter = f"(sAMAccountName={username})"
            search_base = settings.ldap_base_dn
            result = conn.search_s(search_base, ldap.SCOPE_SUBTREE, search_filter)

            if not result:
                return None

            # Get user DN
            user_dn = result[0][0]

            # Try to bind with user credentials
            try:
                user_conn = ldap.initialize(settings.ldap_server)
                user_conn.set_option(ldap.OPT_REFERRALS, 0)
                user_conn.simple_bind_s(user_dn, password)

                # Get user attributes
                attrs = result[0][1]
                return {
                    "username": username,
                    "email": attrs.get("mail", [b""])[0].decode("utf-8") or f"{username}@company.com",
                    "full_name": attrs.get("displayName", [b""])[0].decode("utf-8") or username,
                }
            except ldap.INVALID_CREDENTIALS:
                return None
            finally:
                # Only unbind if connection was successfully created
                if user_conn is not None:
                    try:
                        user_conn.unbind()
                    except Exception:
                        pass  # Ignore errors during cleanup

        except Exception as e:
            # Log error in production
            print(f"LDAP authentication error: {e}")
            return None
        finally:
            # Only unbind if connection was successfully created
            if conn is not None:
                try:
                    conn.unbind()
                except Exception:
                    pass  # Ignore errors during cleanup

    @staticmethod
    def get_or_create_user(db: Session, ldap_user_info: dict) -> User:
        """
        Get existing user or create new user from LDAP info.

        Args:
            db: Database session
            ldap_user_info: User information from LDAP

        Returns:
            User: User object
        """
        user = db.query(User).filter(User.username == ldap_user_info["username"]).first()

        if not user:
            user = User(
                username=ldap_user_info["username"],
                email=ldap_user_info["email"],
                full_name=ldap_user_info["full_name"],
                role=UserRole.MEMBER,
                is_active=True,
            )
            db.add(user)
            # Set last_login for new users
            user.last_login = datetime.now(UTC)
            db.commit()
            db.refresh(user)
        else:
            # Update last login timestamp for existing users
            user.last_login = datetime.now(UTC)
            db.commit()
            db.refresh(user)

        return user

    @staticmethod
    def authenticate_local(db: Session, username: str, password: str) -> Optional[User]:
        """
        Authenticate user with local credentials.

        Args:
            db: Database session
            username: Username or email
            password: Plain text password

        Returns:
            User: User object if authentication succeeds, None otherwise
        """
        # Try username first, then email
        user = db.query(User).filter(
            (User.username == username) | (User.email == username)
        ).first()

        if not user:
            return None

        # Check if user has local auth enabled
        if user.auth_method != "local" or not user.password_hash:
            return None

        # Verify password
        if not PasswordService.verify_password(password, user.password_hash):
            return None

        # Check if account is active
        if not user.is_active:
            return None

        # Update last login
        user.last_login = datetime.now(UTC)
        db.commit()
        db.refresh(user)

        return user

    @staticmethod
    def create_access_token(user_id: UUID, remember_me: bool = False) -> str:
        """
        Create JWT access token for user.

        Args:
            user_id: User UUID
            remember_me: If True, use longer expiry for remember me

        Returns:
            str: JWT access token
        """
        if remember_me:
            expire_minutes = settings.remember_me_expiry_days * 24 * 60
        else:
            expire_minutes = settings.access_token_expire_minutes

        expire = datetime.now(UTC) + timedelta(minutes=expire_minutes)
        to_encode = {"sub": str(user_id), "exp": expire}
        encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
        return encoded_jwt

    @staticmethod
    def create_pending_mfa_token(user_id: UUID) -> str:
        """
        Create a temporary JWT token for pending MFA verification.

        This token can only be used to complete MFA verification, not for API access.

        Args:
            user_id: User UUID

        Returns:
            str: JWT token for pending MFA verification
        """
        # Short expiry for pending MFA (10 minutes)
        expire = datetime.now(UTC) + timedelta(minutes=10)
        to_encode = {
            "sub": str(user_id),
            "exp": expire,
            "pending_mfa": True,  # Mark as pending MFA token
        }
        encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
        return encoded_jwt

    @staticmethod
    def verify_pending_mfa_token(token: str) -> Optional[UUID]:
        """
        Verify and extract user_id from pending MFA token.

        Args:
            token: Pending MFA JWT token

        Returns:
            UUID: User ID if token is valid, None otherwise
        """
        try:
            payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
            if not payload.get("pending_mfa"):
                return None
            user_id_str = payload.get("sub")
            if user_id_str is None:
                return None
            return UUID(user_id_str)
        except (JWTError, ValueError):
            return None

    @staticmethod
    def generate_reset_token() -> str:
        """
        Generate a secure password reset token.

        Returns:
            str: Secure random token
        """
        return secrets.token_urlsafe(32)

    @staticmethod
    def generate_verification_token() -> str:
        """
        Generate a secure email verification token.

        Returns:
            str: Secure random token
        """
        return secrets.token_urlsafe(32)

