# Core application settings loaded from environment variables via pydantic-settings.
import os
from pathlib import Path

from pydantic_settings import BaseSettings

_app_env = os.getenv("APP_ENV", "development")
API_SERVICE_DIR = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = API_SERVICE_DIR / "scripts"
UPLOADS_DIR = API_SERVICE_DIR / "uploads"
RESUME_UPLOADS_DIR = UPLOADS_DIR / "resumes"
AUTOMATION_UPLOADS_DIR = UPLOADS_DIR / "automation"


class Settings(BaseSettings):
    app_env: str = "development"
    app_name: str = "Artemis API"
    secret_key: str = "change_me"

    database_url: str = "postgresql://artemis:artemis@localhost:5433/artemis"
    redis_url: str = "redis://localhost:6379/0"

    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24  # 1 day
    refresh_token_expire_days: int = 30

    storage_backend: str = "local"
    aws_access_key_id: str | None = None
    aws_secret_access_key: str | None = None
    aws_session_token: str | None = None
    aws_region: str = "us-east-1"
    s3_bucket_name: str | None = None
    s3_key_prefix: str = "resumes"

    groq_api_key: str | None = None
    groq_model: str = "llama-3.3-70b-versatile"

    email_backend: str = "console"
    sendgrid_api_key: str | None = None
    from_email: str = "noreply@artemis.dev"

    allowed_origins: list[str] = ["http://localhost:3000", "http://localhost:5173"]
    api_base_url: str | None = None  # e.g. https://api.artemis.dev — used to build absolute URLs behind a proxy

    sentry_dsn: str | None = None
    sentry_environment: str = "development"

    enable_resume_parser: bool = True
    enable_automation: bool = True
    save_screenshots: bool = False
    automation_max_concurrent_sessions: int = 4
    automation_max_concurrent_sessions_per_user: int = 1
    automation_session_limit_ttl_seconds: int = 3600
    max_pipeline_retries: int = 3
    job_scan_interval_hours: int = 24

    class Config:
        env_file = (".env", f".env.{_app_env}")
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()
