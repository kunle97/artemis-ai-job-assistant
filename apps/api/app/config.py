from pydantic import BaseModel
import os


class Settings(BaseModel):
    app_name: str = os.getenv("APP_NAME", "Artemis API")
    database_url: str = os.getenv(
        "DATABASE_URL",
        "postgresql://artemis:artemis@localhost:5432/artemis",
    )
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    secret_key: str = os.getenv("SECRET_KEY", "change_me")


settings = Settings()
