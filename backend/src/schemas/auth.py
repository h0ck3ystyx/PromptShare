"""Authentication-related Pydantic schemas."""

from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class UserRegister(BaseModel):
    """Schema for user registration."""

    email: EmailStr = Field(..., description="User email address")
    username: str = Field(..., min_length=3, max_length=100, description="Username (3-100 characters)")
    full_name: str = Field(..., min_length=1, max_length=255, description="Full name")
    password: str = Field(..., min_length=8, description="Password (minimum 8 characters)")
    remember_me: bool = Field(False, description="Remember me option")


class PasswordResetRequest(BaseModel):
    """Schema for requesting password reset."""

    email: EmailStr = Field(..., description="Email address for password reset")


class PasswordReset(BaseModel):
    """Schema for resetting password."""

    token: str = Field(..., description="Password reset token")
    new_password: str = Field(..., min_length=8, description="New password (minimum 8 characters)")


class PasswordChange(BaseModel):
    """Schema for changing password (authenticated user)."""

    current_password: str = Field(..., description="Current password")
    new_password: str = Field(..., min_length=8, description="New password (minimum 8 characters)")


class EmailVerificationRequest(BaseModel):
    """Schema for requesting email verification."""

    token: str = Field(..., description="Email verification token")


class MFAEnrollRequest(BaseModel):
    """Schema for MFA enrollment request."""

    password: str = Field(..., description="User password for verification")


class MFAVerify(BaseModel):
    """Schema for MFA verification."""

    pending_token: str = Field(..., description="Pending MFA token from login")
    code: str = Field(..., min_length=6, max_length=6, description="6-digit MFA code")
    remember_device: bool = Field(False, description="Remember this device")
    device_fingerprint: Optional[str] = Field(None, description="Device fingerprint for trusted device")
    device_name: Optional[str] = Field(None, description="Device name for trusted device")


class MFADisableRequest(BaseModel):
    """Schema for disabling MFA."""

    password: str = Field(..., description="User password for verification")
    code: Optional[str] = Field(None, min_length=6, max_length=6, description="MFA code if MFA is enabled")


class TrustedDeviceInfo(BaseModel):
    """Schema for trusted device information."""

    id: UUID
    device_name: str
    ip_address: Optional[str]
    created_at: str
    last_used: str

    model_config = {"from_attributes": True}


class UserSessionInfo(BaseModel):
    """Schema for user session information."""

    id: UUID
    device_info: Optional[str]
    ip_address: Optional[str]
    is_active: bool
    created_at: str
    last_activity: str
    expires_at: str

    model_config = {"from_attributes": True}


class SecurityDashboardResponse(BaseModel):
    """Schema for security dashboard response."""

    mfa_enabled: bool
    email_verified: bool
    active_sessions: list[UserSessionInfo]
    trusted_devices: list[TrustedDeviceInfo]
    recent_auth_events: list[dict]  # Simplified for now


class PasswordStrengthResponse(BaseModel):
    """Schema for password strength validation response."""

    valid: bool
    score: int = Field(..., ge=0, le=4, description="Password strength score (0-4)")
    feedback: list[str] = Field(..., description="Feedback messages for password improvement")

