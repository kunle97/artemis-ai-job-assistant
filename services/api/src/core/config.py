# Core application settings loaded from environment variables via pydantic-settings.
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_env: str = "development"
    app_name: str = "Artemis API"
    secret_key: str = "change_me"

    database_url: str = "postgresql://artemis:artemis@localhost:5433/artemis"
    redis_url: str = "redis://localhost:6379/0"

    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    storage_backend: str = "local"
    aws_access_key_id: str | None = None
    aws_secret_access_key: str | None = None
    aws_region: str = "us-east-1"
    s3_bucket_name: str | None = None
    s3_key_prefix: str = "resumes"

    openai_api_key: str | None = None

    email_backend: str = "console"
    sendgrid_api_key: str | None = None
    from_email: str = "noreply@artemis.dev"

    sentry_dsn: str | None = None
    sentry_environment: str = "development"

    enable_resume_parser: bool = True
    enable_automation: bool = True

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()
