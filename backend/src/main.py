"""FastAPI application entry point."""

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

from src.middleware import TimingMiddleware
from src.middleware.rate_limit import RateLimitMiddleware
from src.routers import (
    analytics,
    auth,
    categories,
    collections,
    comments,
    faqs,
    follows,
    notifications,
    onboarding,
    prompts,
    ratings,
    search,
    upvotes,
    users,
)

app = FastAPI(
    title=settings.app_name,
    description=(
        "Internal prompt-sharing web application for employees to discover, submit, "
        "and collaborate on prompts for AI tools (GitHub Copilot, O365 Copilot, Cursor, Claude).\n\n"
        "## Features\n\n"
        "- **Prompt Management**: Create, update, and browse prompts with categories and platform tags\n"
        "- **Search & Discovery**: Full-text search with filters for platform, category, and keywords\n"
        "- **Collaboration**: Comments, ratings, and upvotes on prompts\n"
        "- **Collections**: Curated sets of prompts organized by theme or use case\n"
        "- **Notifications**: Get notified about new prompts in categories you follow\n"
        "- **Analytics**: Track usage statistics (views, copies, searches) - Admin only\n"
        "- **Onboarding**: Get started guides, best practices, and FAQs\n\n"
        "## Authentication\n\n"
        "All endpoints except `/api/onboarding` and `/api/faqs` (read-only) require authentication via LDAP/Active Directory.\n\n"
        "## Documentation\n\n"
        "- Interactive API docs: `/api/docs` (Swagger UI)\n"
        "- Alternative docs: `/api/redoc` (ReDoc)\n"
        "- Onboarding materials: `/api/onboarding`\n"
        "- Best practices: `/api/onboarding/best-practices`\n"
    ),
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,  # Converted from comma-separated string
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom middleware
app.add_middleware(TimingMiddleware)
app.add_middleware(RateLimitMiddleware)

# Include routers
app.include_router(auth.router, prefix="/api")
app.include_router(prompts.router, prefix="/api")
app.include_router(categories.router, prefix="/api")
app.include_router(search.router, prefix="/api")
app.include_router(comments.router, prefix="/api")
app.include_router(ratings.router, prefix="/api")
app.include_router(upvotes.router, prefix="/api")
app.include_router(users.router, prefix="/api")
app.include_router(follows.router, prefix="/api")
app.include_router(notifications.router, prefix="/api")
app.include_router(analytics.router, prefix="/api")
app.include_router(collections.router, prefix="/api")
app.include_router(faqs.router, prefix="/api")
app.include_router(onboarding.router, prefix="/api")


def mask_sensitive_value(value: str, show_length: bool = True) -> str:
    """Mask sensitive values for logging."""
    if not value:
        return "***"
    if len(value) <= 4:
        return "***"
    if show_length:
        return f"{value[:2]}...{value[-2:]} (length: {len(value)})"
    return f"{value[:2]}...{value[-2:]}"


@app.on_event("startup")
async def startup_event():
    """Log environment variables on application startup."""
    logger.info("=" * 80)
    logger.info("Application Starting - Environment Configuration")
    logger.info("=" * 80)
    
    # Application settings
    logger.info(f"App Name: {settings.app_name}")
    logger.info(f"App Environment: {settings.app_env}")
    logger.info(f"Debug Mode: {settings.debug}")
    logger.info(f"App URL: {settings.app_url}")
    
    # Database
    db_url_masked = settings.database_url
    if "@" in db_url_masked:
        # Mask password in database URL (format: postgresql://user:password@host/db)
        parts = db_url_masked.split("@")
        if len(parts) == 2:
            auth_part = parts[0]
            if ":" in auth_part:
                user_pass = auth_part.split("://", 1)[1] if "://" in auth_part else auth_part
                if ":" in user_pass:
                    user, _ = user_pass.split(":", 1)
                    db_url_masked = f"{auth_part.split('://')[0]}://{user}:***@{parts[1]}"
    logger.info(f"Database URL: {db_url_masked}")
    
    # LDAP/AD
    logger.info(f"LDAP Server: {settings.ldap_server}")
    logger.info(f"LDAP Base DN: {settings.ldap_base_dn}")
    logger.info(f"LDAP User DN: {settings.ldap_user_dn}")
    logger.info(f"LDAP Password: {mask_sensitive_value(settings.ldap_password)}")
    
    # Security
    logger.info(f"Secret Key: {mask_sensitive_value(settings.secret_key)}")
    logger.info(f"JWT Algorithm: {settings.algorithm}")
    logger.info(f"Access Token Expiry: {settings.access_token_expire_minutes} minutes")
    
    # Redis
    logger.info(f"Redis URL: {settings.redis_url}")
    logger.info(f"Celery Broker URL: {settings.celery_broker_url}")
    logger.info(f"Celery Result Backend: {settings.celery_result_backend}")
    
    # Email
    logger.info(f"Email Enabled: {settings.email_enabled}")
    if settings.email_enabled:
        logger.info(f"SMTP Host: {settings.email_smtp_host}")
        logger.info(f"SMTP Port: {settings.email_smtp_port}")
        logger.info(f"SMTP User: {settings.email_smtp_user}")
        logger.info(f"SMTP Password: {mask_sensitive_value(settings.email_smtp_password)}")
        logger.info(f"Email From: {settings.email_from_address} ({settings.email_from_name})")
    
    # Local Authentication
    logger.info(f"Local Auth Enabled: {settings.local_auth_enabled}")
    logger.info(f"Password Hash Rounds: {settings.password_hash_rounds}")
    
    # MFA
    logger.info(f"MFA Enabled: {settings.mfa_enabled}")
    if settings.mfa_enabled:
        logger.info(f"MFA Code Expiry: {settings.mfa_code_expiry_minutes} minutes")
        logger.info(f"MFA Trusted Device Days: {settings.mfa_trusted_device_days}")
    
    # Password Reset & Verification
    logger.info(f"Password Reset Token Expiry: {settings.password_reset_token_expiry_hours} hours")
    logger.info(f"Email Verification Token Expiry: {settings.email_verification_token_expiry_hours} hours")
    
    # Rate Limiting
    logger.info(f"Auth Rate Limiting Enabled: {settings.auth_rate_limit_enabled}")
    if settings.auth_rate_limit_enabled:
        logger.info(f"Rate Limit: {settings.auth_rate_limit_per_minute} per minute, {settings.auth_rate_limit_per_hour} per hour")
    
    # Session Management
    logger.info(f"Session Expiry: {settings.session_expiry_hours} hours")
    logger.info(f"Remember Me Expiry: {settings.remember_me_expiry_days} days")
    
    # CORS
    logger.info(f"CORS Origins: {settings.cors_origins}")
    
    # AWS
    logger.info(f"AWS Region: {settings.aws_region}")
    logger.info(f"AWS Secrets Manager Enabled: {settings.aws_secrets_manager_enabled}")
    
    logger.info("=" * 80)


@app.get("/", summary="Root endpoint")
async def root() -> dict:
    """
    Root endpoint for health check.

    Returns:
        dict: Application information
    """
    return {
        "name": settings.app_name,
        "version": "1.0.0",
        "status": "running",
    }


@app.get("/api/health", summary="Health check endpoint")
async def health_check() -> dict:
    """
    Health check endpoint.

    Returns:
        dict: Health status
    """
    return {"status": "healthy"}

