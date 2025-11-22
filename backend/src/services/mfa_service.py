"""Multi-factor authentication service."""

import secrets
from datetime import UTC, datetime, timedelta
from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from src.config import settings
from src.models.auth_token import MFACode
from src.models.trusted_device import TrustedDevice
from src.models.user import User
from src.services.email_service import EmailService


class MFAService:
    """Service for handling MFA operations."""

    @staticmethod
    def generate_mfa_code() -> str:
        """
        Generate a 6-digit MFA code.

        Returns:
            str: 6-digit MFA code
        """
        return f"{secrets.randbelow(1000000):06d}"

    @staticmethod
    def create_mfa_code(db: Session, user_id: UUID) -> str:
        """
        Create and store an MFA code for a user.

        Args:
            db: Database session
            user_id: User ID

        Returns:
            str: Generated MFA code
        """
        # Invalidate any existing unused codes
        db.query(MFACode).filter(
            MFACode.user_id == user_id,
            MFACode.used == False,
            MFACode.expires_at > datetime.now(UTC),
        ).update({"used": True})

        # Generate new code
        code = MFAService.generate_mfa_code()
        expires_at = datetime.now(UTC) + timedelta(minutes=settings.mfa_code_expiry_minutes)

        mfa_code = MFACode(
            user_id=user_id,
            code=code,
            expires_at=expires_at,
        )
        db.add(mfa_code)
        db.commit()

        return code

    @staticmethod
    def verify_mfa_code(db: Session, user_id: UUID, code: str) -> bool:
        """
        Verify an MFA code for a user.

        Args:
            db: Database session
            user_id: User ID
            code: MFA code to verify

        Returns:
            bool: True if code is valid, False otherwise
        """
        mfa_code = db.query(MFACode).filter(
            MFACode.user_id == user_id,
            MFACode.code == code,
            MFACode.used == False,
            MFACode.expires_at > datetime.now(UTC),
        ).first()

        if not mfa_code:
            return False

        # Mark code as used
        mfa_code.used = True
        db.commit()

        return True

    @staticmethod
    async def send_mfa_code(db: Session, user: User) -> bool:
        """
        Generate and send MFA code via email.

        Args:
            db: Database session
            user: User to send code to

        Returns:
            bool: True if code was sent successfully
        """
        if not settings.email_enabled:
            return False

        code = MFAService.create_mfa_code(db, user.id)

        # Send email
        subject = "Your PromptShare MFA Code"
        body = f"""
        Your MFA verification code is: {code}
        
        This code will expire in {settings.mfa_code_expiry_minutes} minutes.
        
        If you didn't request this code, please ignore this email.
        """
        return await EmailService.send_email(user.email, subject, body)

    @staticmethod
    def is_device_trusted(db: Session, user_id: UUID, device_fingerprint: str) -> bool:
        """
        Check if a device is trusted for a user.

        Args:
            db: Database session
            user_id: User ID
            device_fingerprint: Device fingerprint

        Returns:
            bool: True if device is trusted, False otherwise
        """
        device = db.query(TrustedDevice).filter(
            TrustedDevice.user_id == user_id,
            TrustedDevice.device_fingerprint == device_fingerprint,
        ).first()

        if not device:
            return False

        # Check if device trust has expired
        expiry_date = device.last_used + timedelta(days=settings.mfa_trusted_device_days)
        if datetime.now(UTC) > expiry_date:
            # Remove expired trusted device
            db.delete(device)
            db.commit()
            return False

        # Update last used
        device.last_used = datetime.now(UTC)
        db.commit()

        return True

    @staticmethod
    def add_trusted_device(
        db: Session,
        user_id: UUID,
        device_name: str,
        device_fingerprint: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> TrustedDevice:
        """
        Add a trusted device for a user.

        Args:
            db: Database session
            user_id: User ID
            device_name: User-friendly device name
            device_fingerprint: Unique device fingerprint
            ip_address: IP address
            user_agent: User agent string

        Returns:
            TrustedDevice: Created trusted device
        """
        # Remove existing device with same fingerprint
        db.query(TrustedDevice).filter(
            TrustedDevice.device_fingerprint == device_fingerprint,
        ).delete()

        device = TrustedDevice(
            user_id=user_id,
            device_name=device_name,
            device_fingerprint=device_fingerprint,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        db.add(device)
        db.commit()
        db.refresh(device)

        return device

    @staticmethod
    def remove_trusted_device(db: Session, user_id: UUID, device_id: UUID) -> bool:
        """
        Remove a trusted device.

        Args:
            db: Database session
            user_id: User ID
            device_id: Device ID to remove

        Returns:
            bool: True if device was removed, False if not found
        """
        device = db.query(TrustedDevice).filter(
            TrustedDevice.id == device_id,
            TrustedDevice.user_id == user_id,
        ).first()

        if not device:
            return False

        db.delete(device)
        db.commit()
        return True

    @staticmethod
    def get_user_trusted_devices(db: Session, user_id: UUID) -> list[TrustedDevice]:
        """
        Get all trusted devices for a user.

        Args:
            db: Database session
            user_id: User ID

        Returns:
            list[TrustedDevice]: List of trusted devices
        """
        # Remove expired devices
        expiry_threshold = datetime.now(UTC) - timedelta(days=settings.mfa_trusted_device_days)
        db.query(TrustedDevice).filter(
            TrustedDevice.user_id == user_id,
            TrustedDevice.last_used < expiry_threshold,
        ).delete()

        devices = db.query(TrustedDevice).filter(
            TrustedDevice.user_id == user_id,
        ).all()

        return devices

