"""
Database model registry.

This module ensures all SQLAlchemy models are imported so that
they are registered with the global Base metadata.

Any time a new model is added, it must be imported here so that
`Base.metadata.create_all()` can detect and create its table.
"""

from src.domain.auth.models import User
from src.domain.profile.models import CandidateProfile
from src.domain.resume.models import Resume
from src.domain.jobs.models import Job
from src.domain.applications.models import Application
from src.domain.application_answers.models import ApplicationAnswer
from src.domain.application_answers.intents.models import ApplicationAnswerIntent

__all__ = [
    "User",
    "CandidateProfile",
    "Resume",
    "Job",
    "Application",
    "ApplicationAnswer",
    "ApplicationAnswerIntent",
]