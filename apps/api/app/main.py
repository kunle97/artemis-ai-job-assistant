"""
Main FastAPI application entrypoint.

Registers Artemis API routes and creates the application instance.
"""

from fastapi import FastAPI
from app.api.routes.health import router as health_router
from app.api.routes.profile import router as profile_router
from app.api.routes.auth import router as auth_router

app = FastAPI(title="Artemis API")

app.include_router(health_router)
app.include_router(auth_router)
app.include_router(profile_router)