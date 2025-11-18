"""Authentication service for LDAP/AD integration."""

import ldap
from datetime import UTC, datetime, timedelta
from typing import Optional
from uuid import UUID

from jose import jwt
from sqlalchemy.orm import Session

from src.config import settings
from src.models.user import User
from src.constants import UserRole


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
            db.commit()
            db.refresh(user)
        else:
            # Update last login
            user.last_login = datetime.now(UTC)
            db.commit()
            db.refresh(user)

        return user

    @staticmethod
    def create_access_token(user_id: UUID) -> str:
        """
        Create JWT access token for user.

        Args:
            user_id: User UUID

        Returns:
            str: JWT access token
        """
        expire = datetime.now(UTC) + timedelta(minutes=settings.access_token_expire_minutes)
        to_encode = {"sub": str(user_id), "exp": expire}
        encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
        return encoded_jwt

