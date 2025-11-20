"""Application configuration management."""

from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Application
    app_name: str = "PromptShare"
    app_env: str = "development"
    debug: bool = True

    # Database
    database_url: str  # Required - must be set in .env file

    # LDAP/AD
    ldap_server: str  # Required - must be set in .env file
    ldap_base_dn: str  # Required - must be set in .env file
    ldap_user_dn: str  # Required - must be set in .env file
    ldap_password: str  # Required - must be set in .env file

    # Security
    secret_key: str  # Required - must be set in .env file
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Celery
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/0"

    # Email (SMTP)
    email_enabled: bool = False
    email_smtp_host: str = "smtp.gmail.com"
    email_smtp_port: int = 587
    email_smtp_user: str = ""
    email_smtp_password: str = ""
    email_from_address: str = "noreply@promptshare.com"
    email_from_name: str = "PromptShare"

    # CORS - stored as comma-separated string in env, converted to list
    cors_origins: str = "http://localhost:5173,http://localhost:3000"

    # AWS (for production)
    aws_region: str = "us-east-1"
    aws_secrets_manager_enabled: bool = False

    @property
    def cors_origins_list(self) -> List[str]:
        """Get CORS origins as a list."""
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


settings = Settings()

