# Core application settings loaded from environment variables via pydantic-settings.
import os

from pydantic_settings import BaseSettings

_app_env = os.getenv("APP_ENV", "development")


class Settings(BaseSettings):
    app_env: str = "development"
    app_name: str = "Artemis API"
    secret_key: str = "change_me"

    database_url: str = "postgresql://artemis:artemis@localhost:5433/artemis"
    redis_url: str = "redis://localhost:6379/0"

    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 30

    storage_backend: str = "local"
    aws_access_key_id: str | None = None
    aws_secret_access_key: str | None = None
    aws_region: str = "us-east-1"
    s3_bucket_name: str | None = None
    s3_key_prefix: str = "resumes"

    groq_api_key: str | None = None
    groq_model: str = "llama-3.3-70b-versatile"

    email_backend: str = "console"
    sendgrid_api_key: str | None = None
    from_email: str = "noreply@artemis.dev"

    allowed_origins: list[str] = ["http://localhost:3000", "http://localhost:5173"]
    revoked_token_cleanup_retention_days: int = 0

    sentry_dsn: str | None = None
    sentry_environment: str = "development"

    enable_resume_parser: bool = True
    enable_automation: bool = True
    save_screenshots: bool = False

    class Config:
        env_file = (".env", f".env.{_app_env}")
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()
