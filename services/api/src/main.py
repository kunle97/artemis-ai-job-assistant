"""
Main FastAPI application entrypoint.

Registers Artemis API routes and creates the application instance.
"""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from src.infrastructure.db import register_models
from src.core.config import settings
from src.core.rate_limiter import limiter

from src.routes.health import router as health_router
from src.routes.profile import router as profile_router
from src.routes.auth import router as auth_router
from src.routes.resumes import router as resumes_router
from src.routes.jobs import router as jobs_router
from src.routes.applications import router as applications_router
from src.routes.application_answers import router as application_answers_router
from src.routes.application_answer_resolution import (
    router as application_answer_resolution_router,
)
from src.routes.application_readiness import router as application_readiness_router
from src.routes.application_planning import router as application_planning_router
from src.routes.automation import router as automation_router
from src.routes.automation_planning import router as automation_planning_router
from src.routes.automation_fill import router as automation_fill_router
from src.routes.automation_manual_fill import router as automation_manual_fill_router
from src.routes.automation_test_fill import router as automation_test_fill_router


def _validate_security_settings() -> None:
    if settings.secret_key == "change_me":
        raise RuntimeError("SECRET_KEY must be set to a secure value before running")


_validate_security_settings()
register_models()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

# Promote fill handler to DEBUG so combobox fill steps are visible in logs.
logging.getLogger("src.domain.automation.fill.handlers.select_like").setLevel(logging.DEBUG)
app = FastAPI(title="Artemis API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.include_router(health_router)
app.include_router(auth_router)
app.include_router(profile_router)
app.include_router(resumes_router)
app.include_router(jobs_router)
app.include_router(applications_router)
app.include_router(application_answers_router)
app.include_router(application_answer_resolution_router)
app.include_router(application_readiness_router)
app.include_router(application_planning_router)
app.include_router(automation_router)
app.include_router(automation_planning_router)
app.include_router(automation_fill_router)
app.include_router(automation_test_fill_router)
app.include_router(automation_manual_fill_router)