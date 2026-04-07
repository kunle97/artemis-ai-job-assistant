"""
Main FastAPI application entrypoint.

Registers Artemis API routes and creates the application instance.
"""

from fastapi import FastAPI

# Register models so SQLAlchemy metadata is populated before startup.
import src.domain.auth.models  # noqa: F401
import src.domain.profile.models  # noqa: F401
import src.domain.resume.models  # noqa: F401

from src.routes.health import router as health_router
from src.routes.profile import router as profile_router
from src.routes.auth import router as auth_router
from src.routes.resumes import router as resumes_router

app = FastAPI(title="Artemis API")

app.include_router(health_router)
app.include_router(auth_router)
app.include_router(profile_router)
app.include_router(resumes_router)