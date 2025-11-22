"""Email notification service."""

import logging
from typing import Optional
from uuid import UUID

import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from src.config import settings
from src.constants import NotificationType
from src.models.user import User

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending email notifications."""

    @staticmethod
    def is_enabled() -> bool:
        """
        Check if email notifications are enabled.

        Returns:
            bool: True if email is enabled and configured
        """
        return (
            settings.email_enabled
            and settings.email_smtp_user
            and settings.email_smtp_password
        )

    @staticmethod
    async def send_notification_email(
        user_id: UUID,
        notification_type: NotificationType,
        message: str,
        prompt_id: Optional[UUID] = None,
    ) -> None:
        """
        Send an email notification to a user.

        Args:
            user_id: ID of the user to notify
            notification_type: Type of notification
            message: Notification message
            prompt_id: Optional prompt ID

        Raises:
            ValueError: If email is not enabled or user not found
        """
        if not EmailService.is_enabled():
            raise ValueError("Email notifications are not enabled")

        # Get user from database
        from src.database import SessionLocal
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                raise ValueError(f"User {user_id} not found")

            # Build email
            subject = EmailService._get_email_subject(notification_type)
            body = EmailService._build_email_body(
                user=user,
                notification_type=notification_type,
                message=message,
                prompt_id=prompt_id,
            )

            # Send email
            await EmailService._send_email_async(
                to_email=user.email,
                to_name=user.full_name,
                subject=subject,
                body=body,
            )
        finally:
            db.close()

    @staticmethod
    def _get_email_subject(notification_type: NotificationType) -> str:
        """
        Get email subject based on notification type.

        Args:
            notification_type: Type of notification

        Returns:
            str: Email subject
        """
        subjects = {
            NotificationType.NEW_PROMPT: "New Prompt Published - PromptShare",
            NotificationType.COMMENT: "New Comment on Your Prompt - PromptShare",
            NotificationType.UPDATE: "Prompt Updated - PromptShare",
        }
        return subjects.get(notification_type, "Notification from PromptShare")

    @staticmethod
    def _build_email_body(
        user: User,
        notification_type: NotificationType,
        message: str,
        prompt_id: Optional[UUID] = None,
    ) -> str:
        """
        Build HTML email body.

        Args:
            user: User receiving the notification
            notification_type: Type of notification
            message: Notification message
            prompt_id: Optional prompt ID

        Returns:
            str: HTML email body
        """
        app_url = "http://localhost:5173"  # TODO: Get from config
        prompt_link = f"{app_url}/prompts/{prompt_id}" if prompt_id else app_url

        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #4F46E5; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; background-color: #f9fafb; }}
                .button {{ display: inline-block; padding: 12px 24px; background-color: #4F46E5; color: white; text-decoration: none; border-radius: 4px; margin-top: 20px; }}
                .footer {{ padding: 20px; text-align: center; color: #6b7280; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>PromptShare</h1>
                </div>
                <div class="content">
                    <p>Hello {user.full_name},</p>
                    <p>{message}</p>
        """

        if prompt_id:
            html_body += f"""
                    <a href="{prompt_link}" class="button">View Prompt</a>
            """

        html_body += f"""
                </div>
                <div class="footer">
                    <p>You're receiving this because you're following categories or have activity on PromptShare.</p>
                    <p>Manage your notification preferences in your account settings.</p>
                </div>
            </div>
        </body>
        </html>
        """

        return html_body

    @staticmethod
    async def send_email(to_email: str, subject: str, body: str) -> bool:
        """
        Send email asynchronously (for MFA codes, password resets, etc.).

        Args:
            to_email: Recipient email address
            subject: Email subject
            body: Email body (plain text)

        Returns:
            bool: True if email was sent successfully, False otherwise
        """
        if not EmailService.is_enabled():
            logger.warning(
                "Email service is disabled. Cannot send email to %s",
                to_email,
            )
            return False

        try:
            await EmailService._send_email_async(to_email, "", subject, body)
            logger.info(
                "Email sent successfully to %s with subject: %s",
                to_email,
                subject,
            )
            return True
        except Exception as e:
            logger.error(
                "Failed to send email to %s: %s (type: %s)",
                to_email,
                str(e),
                type(e).__name__,
                exc_info=True,
            )
            return False

    @staticmethod
    async def _send_email_async(
        to_email: str,
        to_name: str,
        subject: str,
        body: str,
    ) -> None:
        """
        Send email via SMTP.

        Args:
            to_email: Recipient email address
            to_name: Recipient name
            subject: Email subject
            body: HTML email body

        Raises:
            Exception: If email sending fails
        """
        # Create message
        message = MIMEMultipart("alternative")
        message["From"] = f"{settings.email_from_name} <{settings.email_from_address}>"
        message["To"] = f"{to_name} <{to_email}>"
        message["Subject"] = subject

        # Add HTML body
        html_part = MIMEText(body, "html")
        message.attach(html_part)

        # Send via SMTP
        # Port 465 uses direct SSL/TLS (use_tls=True)
        # Port 587 uses STARTTLS (start_tls=True) - upgrade from plain to TLS
        # Port 25 is typically plain text (no encryption)
        use_tls = settings.email_smtp_port == 465
        start_tls = settings.email_smtp_port == 587
        
        await aiosmtplib.send(
            message,
            hostname=settings.email_smtp_host,
            port=settings.email_smtp_port,
            username=settings.email_smtp_user,
            password=settings.email_smtp_password,
            use_tls=use_tls,
            start_tls=start_tls,
        )

