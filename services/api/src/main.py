"""
Main FastAPI application entrypoint.

Registers Artemis API routes and creates the application instance.
"""

from fastapi import FastAPI

# Ensure all models are registered with SQLAlchemy Base metadata
import src.infrastructure.db  # noqa: F401

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
    
app = FastAPI(title="Artemis API")

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