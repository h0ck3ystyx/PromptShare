"""Authentication router endpoints."""

from datetime import UTC, datetime, timedelta
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Header, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from starlette.concurrency import run_in_threadpool

from src.config import settings
from src.dependencies import CurrentUserDep, DatabaseDep
from src.models.auth_token import EmailVerificationToken, PasswordResetToken
from src.models.trusted_device import TrustedDevice
from src.models.user import User
from src.schemas.auth import (
    EmailVerificationRequest,
    MFADisableRequest,
    MFAEnrollRequest,
    MFAVerify,
    PasswordChange,
    PasswordReset,
    PasswordResetRequest,
    PasswordStrengthResponse,
    SecurityDashboardResponse,
    TrustedDeviceInfo,
    UserRegister,
    UserSessionInfo,
)
from src.schemas.user import Token, UserResponse
from src.services.auth_audit_service import AuthAuditService
from src.services.auth_service import AuthService
from src.services.email_service import EmailService
from src.services.mfa_service import MFAService
from src.services.password_service import PasswordService
from src.services.password_validation_service import PasswordValidationService
from src.services.session_service import SessionService

router = APIRouter(prefix="/auth", tags=["authentication"])


def get_client_ip(request: Request) -> Optional[str]:
    """Extract client IP address from request."""
    ip_address = request.headers.get("X-Forwarded-For")
    if ip_address:
        ip_address = ip_address.split(",")[0].strip()
    else:
        ip_address = request.client.host if request.client else None
    return ip_address


def get_user_agent(request: Request) -> Optional[str]:
    """Extract user agent from request."""
    return request.headers.get("User-Agent")


@router.post("/login", response_model=Token, summary="Login with LDAP/AD or local credentials")
async def login(
    request: Request,
    db: DatabaseDep,
    form_data: OAuth2PasswordRequestForm = Depends(),
) -> Token:
    """
    Authenticate user with LDAP/Active Directory or local credentials.

    Tries local authentication first if enabled, then falls back to LDAP.

    Args:
        request: FastAPI request object
        form_data: OAuth2 form data containing username and password
        db: Database session

    Returns:
        Token: JWT access token

    Raises:
        HTTPException: If authentication fails
    """
    ip_address = get_client_ip(request)
    user_agent = get_user_agent(request)
    user: Optional[User] = None
    auth_method = "unknown"

    # Try local authentication first if enabled
    if settings.local_auth_enabled:
        user = AuthService.authenticate_local(db, form_data.username, form_data.password)
        if user:
            auth_method = "local"

    # Fall back to LDAP if local auth failed or not enabled
    if not user:
        ldap_user_info = await run_in_threadpool(
            AuthService.authenticate_ldap,
            form_data.username,
            form_data.password,
        )

        if ldap_user_info:
            user = AuthService.get_or_create_user(db, ldap_user_info)
            auth_method = "ldap"

    if not user:
        # Log failed login attempt
        AuthAuditService.log_event(
            db=db,
            event_type="login_failed",
            ip_address=ip_address,
            user_agent=user_agent,
            details=f"username={form_data.username}",
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check if user account is active
    if not user.is_active:
        AuthAuditService.log_event(
            db=db,
            event_type="login_blocked_inactive",
            user_id=user.id,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )

    # Check MFA if enabled
    if user.mfa_enabled:
        # Check if device is trusted (skip MFA for trusted devices)
        device_fingerprint = request.headers.get("X-Device-Fingerprint")  # Client should send this
        if device_fingerprint and MFAService.is_device_trusted(db, user.id, device_fingerprint):
            # Device is trusted, proceed with login
            pass
        else:
            # MFA required - send code and return pending token
            await MFAService.send_mfa_code(db, user)

            # Log MFA challenge
            AuthAuditService.log_event(
                db=db,
                event_type="mfa_challenge_sent",
                user_id=user.id,
                ip_address=ip_address,
                user_agent=user_agent,
            )

            # Create pending MFA token (not a full access token)
            pending_token = AuthService.create_pending_mfa_token(user.id)

            return Token(
                access_token=pending_token,
                token_type="bearer",
                mfa_required=True,
            )

    # Log successful login
    AuthAuditService.log_event(
        db=db,
        event_type="login_success",
        user_id=user.id,
        ip_address=ip_address,
        user_agent=user_agent,
        details=f"method={auth_method}",
    )

    # Create access token
    access_token = AuthService.create_access_token(user.id)

    # Create user session
    device_info = user_agent or "Unknown device"
    SessionService.create_session(
        db=db,
        user_id=user.id,
        access_token=access_token,
        ip_address=ip_address,
        user_agent=user_agent,
        device_info=device_info,
    )

    return Token(access_token=access_token, token_type="bearer", mfa_required=False)


@router.get("/me", response_model=UserResponse, summary="Get current user information")
async def get_current_user_info(
    current_user: CurrentUserDep,
) -> UserResponse:
    """
    Get current authenticated user information.

    Args:
        current_user: Current authenticated user from dependency

    Returns:
        UserResponse: Current user information
    """
    return UserResponse.model_validate(current_user)


@router.post("/register", response_model=UserResponse, summary="Register a new user")
async def register(
    request: Request,
    db: DatabaseDep,
    user_data: UserRegister,
) -> UserResponse:
    """
    Register a new user with local authentication.

    Args:
        request: FastAPI request object
        user_data: User registration data
        db: Database session

    Returns:
        UserResponse: Created user information

    Raises:
        HTTPException: If registration fails
    """
    if not settings.local_auth_enabled:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Local authentication is not enabled",
        )

    # Validate password strength
    validation = PasswordValidationService.validate_password_strength(user_data.password)
    if not validation["valid"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Password does not meet requirements: {', '.join(validation['feedback'])}",
        )

    # Check if username or email already exists
    existing_user = db.query(User).filter(
        (User.username == user_data.username) | (User.email == user_data.email)
    ).first()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email already exists",
        )

    # Hash password
    password_hash = PasswordService.hash_password(user_data.password)

    # Create user
    user = User(
        username=user_data.username,
        email=user_data.email,
        full_name=user_data.full_name,
        password_hash=password_hash,
        auth_method="local",
        email_verified=False,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Create email verification token
    token = AuthService.generate_verification_token()
    expires_at = datetime.now(UTC) + timedelta(hours=settings.email_verification_token_expiry_hours)

    verification_token = EmailVerificationToken(
        user_id=user.id,
        token=token,
        expires_at=expires_at,
    )
    db.add(verification_token)
    db.commit()

    # Send verification email
    if settings.email_enabled:
        # Email verification has a GET handler on the backend API
        verification_url = f"{request.base_url}api/auth/verify-email?token={token}"
        subject = "Verify your PromptShare account"
        body = f"""
        Welcome to PromptShare!
        
        Please verify your email address by clicking the link below:
        {verification_url}
        
        This link will expire in {settings.email_verification_token_expiry_hours} hours.
        
        If you didn't create this account, please ignore this email.
        """
        await EmailService.send_email(user.email, subject, body)

    # Log registration
    ip_address = get_client_ip(request)
    user_agent = get_user_agent(request)
    AuthAuditService.log_event(
        db=db,
        event_type="user_registered",
        user_id=user.id,
        ip_address=ip_address,
        user_agent=user_agent,
    )

    return UserResponse.model_validate(user)


def _verify_email_token(db: Session, token: str, request: Request) -> dict:
    """
    Internal function to verify email token.

    Args:
        db: Database session
        token: Verification token
        request: FastAPI request object

    Returns:
        dict: Success message

    Raises:
        HTTPException: If verification fails
    """
    token_obj = db.query(EmailVerificationToken).filter(
        EmailVerificationToken.token == token,
        EmailVerificationToken.used == False,
        EmailVerificationToken.expires_at > datetime.now(UTC),
    ).first()

    if not token_obj:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification token",
        )

    # Mark token as used and verify user email
    token_obj.used = True
    user = db.query(User).filter(User.id == token_obj.user_id).first()
    if user:
        user.email_verified = True
        db.commit()

        # Log verification
        ip_address = get_client_ip(request)
        AuthAuditService.log_event(
            db=db,
            event_type="email_verified",
            user_id=user.id,
            ip_address=ip_address,
        )

    return {"message": "Email verified successfully"}


@router.get("/verify-email", summary="Verify email address (GET)")
async def verify_email_get(
    request: Request,
    db: DatabaseDep,
    token: str,
) -> dict:
    """
    Verify user email address with token from query string (for email links).

    Args:
        request: FastAPI request object
        token: Email verification token from query parameter
        db: Database session

    Returns:
        dict: Success message

    Raises:
        HTTPException: If verification fails
    """
    return _verify_email_token(db, token, request)


@router.post("/verify-email", summary="Verify email address (POST)")
async def verify_email_post(
    request: Request,
    db: DatabaseDep,
    verification_data: EmailVerificationRequest,
) -> dict:
    """
    Verify user email address with token from JSON body.

    Args:
        request: FastAPI request object
        verification_data: Email verification token
        db: Database session

    Returns:
        dict: Success message

    Raises:
        HTTPException: If verification fails
    """
    return _verify_email_token(db, verification_data.token, request)


@router.post("/password-reset-request", summary="Request password reset")
async def password_reset_request(
    request: Request,
    db: DatabaseDep,
    reset_request: PasswordResetRequest,
) -> dict:
    """
    Request a password reset for a user.

    Args:
        request: FastAPI request object
        reset_request: Password reset request data
        db: Database session

    Returns:
        dict: Success message (always returns success to prevent email enumeration)
    """
    user = db.query(User).filter(User.email == reset_request.email).first()

    if user and user.auth_method == "local":
        # Invalidate existing reset tokens
        db.query(PasswordResetToken).filter(
            PasswordResetToken.user_id == user.id,
            PasswordResetToken.used == False,
        ).update({"used": True})

        # Create new reset token
        token = AuthService.generate_reset_token()
        expires_at = datetime.now(UTC) + timedelta(hours=settings.password_reset_token_expiry_hours)

        reset_token = PasswordResetToken(
            user_id=user.id,
            token=token,
            expires_at=expires_at,
        )
        db.add(reset_token)
        db.commit()

        # Send reset email
        if settings.email_enabled:
            # Use frontend URL for password reset link (not API base URL)
            reset_url = f"{settings.app_url}/password-reset?token={token}"
            subject = "Reset your PromptShare password"
            body = f"""
            You requested a password reset for your PromptShare account.
            
            Click the link below to reset your password:
            {reset_url}
            
            This link will expire in {settings.password_reset_token_expiry_hours} hours.
            
            If you didn't request this, please ignore this email.
            """
            await EmailService.send_email(user.email, subject, body)

        # Log reset request
        ip_address = get_client_ip(request)
        AuthAuditService.log_event(
            db=db,
            event_type="password_reset_requested",
            user_id=user.id,
            ip_address=ip_address,
        )

    # Always return success to prevent email enumeration
    return {"message": "If the email exists, a password reset link has been sent"}


@router.post("/password-reset", summary="Reset password with token")
async def password_reset(
    request: Request,
    db: DatabaseDep,
    reset_data: PasswordReset,
) -> dict:
    """
    Reset password using a reset token.

    Args:
        request: FastAPI request object
        reset_data: Password reset data
        db: Database session

    Returns:
        dict: Success message

    Raises:
        HTTPException: If reset fails
    """
    # Validate password strength
    validation = PasswordValidationService.validate_password_strength(reset_data.new_password)
    if not validation["valid"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Password does not meet requirements: {', '.join(validation['feedback'])}",
        )

    token_obj = db.query(PasswordResetToken).filter(
        PasswordResetToken.token == reset_data.token,
        PasswordResetToken.used == False,
        PasswordResetToken.expires_at > datetime.now(UTC),
    ).first()

    if not token_obj:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token",
        )

    # Update password
    user = db.query(User).filter(User.id == token_obj.user_id).first()
    if user:
        user.password_hash = PasswordService.hash_password(reset_data.new_password)
        token_obj.used = True
        db.commit()

        # Log password reset
        ip_address = get_client_ip(request)
        AuthAuditService.log_event(
            db=db,
            event_type="password_reset_completed",
            user_id=user.id,
            ip_address=ip_address,
        )

    return {"message": "Password reset successfully"}


@router.post("/change-password", summary="Change password (authenticated)")
async def change_password(
    request: Request,
    db: DatabaseDep,
    current_user: CurrentUserDep,
    password_data: PasswordChange,
) -> dict:
    """
    Change password for authenticated user.

    Args:
        request: FastAPI request object
        password_data: Password change data
        db: Database session
        current_user: Current authenticated user

    Returns:
        dict: Success message

    Raises:
        HTTPException: If password change fails
    """
    if current_user.auth_method != "local" or not current_user.password_hash:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password change is only available for local authentication",
        )

    # Verify current password
    if not PasswordService.verify_password(password_data.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Current password is incorrect",
        )

    # Validate new password strength
    validation = PasswordValidationService.validate_password_strength(password_data.new_password)
    if not validation["valid"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Password does not meet requirements: {', '.join(validation['feedback'])}",
        )

    # Update password
    current_user.password_hash = PasswordService.hash_password(password_data.new_password)
    db.commit()

    # Log password change
    ip_address = get_client_ip(request)
    AuthAuditService.log_event(
        db=db,
        event_type="password_changed",
        user_id=current_user.id,
        ip_address=ip_address,
    )

    return {"message": "Password changed successfully"}


@router.post("/validate-password", response_model=PasswordStrengthResponse, summary="Validate password strength")
async def validate_password(
    password: str,
) -> PasswordStrengthResponse:
    """
    Validate password strength and return feedback.

    Args:
        password: Password to validate

    Returns:
        PasswordStrengthResponse: Password validation result
    """
    validation = PasswordValidationService.validate_password_strength(password)
    return PasswordStrengthResponse(**validation)


@router.post("/logout", summary="Logout current user")
async def logout(
    request: Request,
    db: DatabaseDep,
    current_user: CurrentUserDep,
    authorization: Optional[str] = Header(None),
) -> dict:
    """
    Logout current user (client should discard token).

    Args:
        request: FastAPI request object
        db: Database session
        current_user: Current authenticated user
        authorization: Authorization header with Bearer token

    Returns:
        dict: Success message
    """
    # Extract token from Authorization header and invalidate session
    if authorization and authorization.startswith("Bearer "):
        token = authorization[7:]  # Remove "Bearer " prefix
        SessionService.invalidate_session(db, token)

    # Log logout event
    ip_address = get_client_ip(request)
    AuthAuditService.log_event(
        db=db,
        event_type="logout",
        user_id=current_user.id,
        ip_address=ip_address,
    )

    return {"message": "Successfully logged out"}


# MFA Endpoints
@router.post("/mfa/enroll", summary="Enroll in MFA")
async def mfa_enroll(
    request: Request,
    db: DatabaseDep,
    current_user: CurrentUserDep,
    enroll_data: MFAEnrollRequest,
) -> dict:
    """
    Enroll user in MFA (email-based).

    Args:
        request: FastAPI request object
        db: Database session
        current_user: Current authenticated user
        enroll_data: MFA enrollment data

    Returns:
        dict: Success message

    Raises:
        HTTPException: If enrollment fails
    """
    if not settings.mfa_enabled:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="MFA is not enabled",
        )

    if current_user.auth_method != "local" or not current_user.password_hash:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MFA is only available for local authentication",
        )

    # Verify password
    if not PasswordService.verify_password(enroll_data.password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Password is incorrect",
        )

    # Enable MFA
    current_user.mfa_enabled = True
    db.commit()

    # Log MFA enrollment
    ip_address = get_client_ip(request)
    AuthAuditService.log_event(
        db=db,
        event_type="mfa_enrolled",
        user_id=current_user.id,
        ip_address=ip_address,
    )

    return {"message": "MFA enabled successfully"}


@router.post("/mfa/verify", response_model=Token, summary="Verify MFA code")
async def mfa_verify(
    request: Request,
    db: DatabaseDep,
    verify_data: MFAVerify,
) -> Token:
    """
    Verify MFA code and complete login (used after initial login with MFA required).

    Args:
        request: FastAPI request object
        db: Database session
        verify_data: MFA verification data

    Returns:
        Token: JWT access token

    Raises:
        HTTPException: If verification fails
    """
    ip_address = get_client_ip(request)
    user_agent = get_user_agent(request)

    # Verify pending MFA token
    user_id = AuthService.verify_pending_mfa_token(verify_data.pending_token)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired pending MFA token",
        )

    # Get user
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    if not user.mfa_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MFA is not enabled for this account",
        )

    # Verify MFA code
    if not MFAService.verify_mfa_code(db, user.id, verify_data.code):
        # Log failed MFA attempt
        AuthAuditService.log_event(
            db=db,
            event_type="mfa_verification_failed",
            user_id=user.id,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired MFA code",
        )

    # MFA verified successfully - record trusted device if requested
    if verify_data.remember_device and verify_data.device_fingerprint:
        device_name = verify_data.device_name or f"Device from {ip_address or 'unknown'}"
        MFAService.add_trusted_device(
            db=db,
            user_id=user.id,
            device_name=device_name,
            device_fingerprint=verify_data.device_fingerprint,
            ip_address=ip_address,
            user_agent=user_agent,
        )

    # Log successful MFA verification
    AuthAuditService.log_event(
        db=db,
        event_type="mfa_verification_success",
        user_id=user.id,
        ip_address=ip_address,
        user_agent=user_agent,
    )

    # Log successful login (completing the MFA flow)
    AuthAuditService.log_event(
        db=db,
        event_type="login_success",
        user_id=user.id,
        ip_address=ip_address,
        user_agent=user_agent,
        details="completed_with_mfa",
    )

    # Create full access token
    access_token = AuthService.create_access_token(user.id)

    # Create user session after MFA verification
    device_info = user_agent or "Unknown device"
    SessionService.create_session(
        db=db,
        user_id=user.id,
        access_token=access_token,
        ip_address=ip_address,
        user_agent=user_agent,
        device_info=device_info,
    )

    return Token(access_token=access_token, token_type="bearer", mfa_required=False)


@router.post("/mfa/disable", summary="Disable MFA")
async def mfa_disable(
    request: Request,
    db: DatabaseDep,
    current_user: CurrentUserDep,
    disable_data: MFADisableRequest,
) -> dict:
    """
    Disable MFA for user.

    Args:
        request: FastAPI request object
        db: Database session
        current_user: Current authenticated user
        disable_data: MFA disable data

    Returns:
        dict: Success message

    Raises:
        HTTPException: If disable fails
    """
    if not current_user.mfa_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MFA is not enabled for this account",
        )

    # Verify password
    if not PasswordService.verify_password(disable_data.password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Password is incorrect",
        )

    # Verify MFA code if provided
    if disable_data.code:
        if not MFAService.verify_mfa_code(db, current_user.id, disable_data.code):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="MFA code is incorrect",
            )

    # Disable MFA
    current_user.mfa_enabled = False
    current_user.mfa_secret = None
    db.commit()

    # Remove all trusted devices
    db.query(TrustedDevice).filter(TrustedDevice.user_id == current_user.id).delete()
    db.commit()

    # Log MFA disable
    ip_address = get_client_ip(request)
    AuthAuditService.log_event(
        db=db,
        event_type="mfa_disabled",
        user_id=current_user.id,
        ip_address=ip_address,
    )

    return {"message": "MFA disabled successfully"}


@router.get("/mfa/status", summary="Get MFA status")
async def mfa_status(
    current_user: CurrentUserDep,
) -> dict:
    """
    Get MFA status for current user.

    Args:
        current_user: Current authenticated user

    Returns:
        dict: MFA status
    """
    return {
        "mfa_enabled": current_user.mfa_enabled,
        "email_verified": current_user.email_verified,
    }


# Security Dashboard Endpoints
@router.get("/security", response_model=SecurityDashboardResponse, summary="Get security dashboard data")
async def get_security_dashboard(
    db: DatabaseDep,
    current_user: CurrentUserDep,
) -> SecurityDashboardResponse:
    """
    Get security dashboard data for current user.

    Args:
        db: Database session
        current_user: Current authenticated user

    Returns:
        SecurityDashboardResponse: Security dashboard data
    """
    from src.models.user_session import UserSession
    from src.models.auth_audit import AuthAuditLog

    # Get active sessions
    sessions = db.query(UserSession).filter(
        UserSession.user_id == current_user.id,
        UserSession.is_active == True,
        UserSession.expires_at > datetime.now(UTC),
    ).order_by(UserSession.last_activity.desc()).all()

    session_info = [
        UserSessionInfo(
            id=session.id,
            device_info=session.device_info,
            ip_address=session.ip_address,
            is_active=session.is_active,
            created_at=session.created_at.isoformat(),
            last_activity=session.last_activity.isoformat(),
            expires_at=session.expires_at.isoformat(),
        )
        for session in sessions
    ]

    # Get trusted devices
    trusted_devices = MFAService.get_user_trusted_devices(db, current_user.id)
    device_info = [
        TrustedDeviceInfo(
            id=device.id,
            device_name=device.device_name,
            ip_address=device.ip_address,
            created_at=device.created_at.isoformat(),
            last_used=device.last_used.isoformat(),
        )
        for device in trusted_devices
    ]

    # Get recent auth events (last 20)
    recent_events = AuthAuditService.get_user_audit_logs(db, current_user.id, limit=20)
    event_info = [
        {
            "event_type": event.event_type,
            "ip_address": event.ip_address,
            "created_at": event.created_at.isoformat(),
            "details": event.details,
        }
        for event in recent_events
    ]

    return SecurityDashboardResponse(
        mfa_enabled=current_user.mfa_enabled,
        email_verified=current_user.email_verified,
        active_sessions=session_info,
        trusted_devices=device_info,
        recent_auth_events=event_info,
    )


@router.get("/sessions", response_model=list[UserSessionInfo], summary="List active sessions")
async def list_sessions(
    db: DatabaseDep,
    current_user: CurrentUserDep,
) -> list[UserSessionInfo]:
    """
    List all active sessions for current user.

    Args:
        db: Database session
        current_user: Current authenticated user

    Returns:
        list[UserSessionInfo]: List of active sessions
    """
    from src.models.user_session import UserSession

    sessions = db.query(UserSession).filter(
        UserSession.user_id == current_user.id,
        UserSession.is_active == True,
        UserSession.expires_at > datetime.now(UTC),
    ).order_by(UserSession.last_activity.desc()).all()

    return [
        UserSessionInfo(
            id=session.id,
            device_info=session.device_info,
            ip_address=session.ip_address,
            is_active=session.is_active,
            created_at=session.created_at.isoformat(),
            last_activity=session.last_activity.isoformat(),
            expires_at=session.expires_at.isoformat(),
        )
        for session in sessions
    ]


@router.delete("/sessions/{session_id}", summary="Revoke a session")
async def revoke_session(
    request: Request,
    db: DatabaseDep,
    current_user: CurrentUserDep,
    session_id: UUID,
) -> dict:
    """
    Revoke (deactivate) a specific session.

    Args:
        db: Database session
        current_user: Current authenticated user
        session_id: Session ID to revoke

    Returns:
        dict: Success message

    Raises:
        HTTPException: If session not found
    """
    from src.models.user_session import UserSession

    session = db.query(UserSession).filter(
        UserSession.id == session_id,
        UserSession.user_id == current_user.id,
    ).first()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )

    session.is_active = False
    db.commit()

    # Log session revocation
    ip_address = get_client_ip(request)
    AuthAuditService.log_event(
        db=db,
        event_type="session_revoked",
        user_id=current_user.id,
        ip_address=ip_address,
    )

    return {"message": "Session revoked successfully"}


@router.get("/devices", response_model=list[TrustedDeviceInfo], summary="List trusted devices")
async def list_trusted_devices(
    db: DatabaseDep,
    current_user: CurrentUserDep,
) -> list[TrustedDeviceInfo]:
    """
    List all trusted devices for current user.

    Args:
        db: Database session
        current_user: Current authenticated user

    Returns:
        list[TrustedDeviceInfo]: List of trusted devices
    """
    devices = MFAService.get_user_trusted_devices(db, current_user.id)

    return [
        TrustedDeviceInfo(
            id=device.id,
            device_name=device.device_name,
            ip_address=device.ip_address,
            created_at=device.created_at.isoformat(),
            last_used=device.last_used.isoformat(),
        )
        for device in devices
    ]


@router.delete("/devices/{device_id}", summary="Remove a trusted device")
async def remove_trusted_device(
    request: Request,
    db: DatabaseDep,
    current_user: CurrentUserDep,
    device_id: UUID,
) -> dict:
    """
    Remove a trusted device.

    Args:
        db: Database session
        current_user: Current authenticated user
        device_id: Device ID to remove

    Returns:
        dict: Success message

    Raises:
        HTTPException: If device not found
    """
    success = MFAService.remove_trusted_device(db, current_user.id, device_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found",
        )

    # Log device removal
    ip_address = get_client_ip(request)
    AuthAuditService.log_event(
        db=db,
        event_type="trusted_device_removed",
        user_id=current_user.id,
        ip_address=ip_address,
    )

    return {"message": "Trusted device removed successfully"}

