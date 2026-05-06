"""
Application scoring routes.

Exposes POST /applications/{application_id}/score to trigger job fit scoring
for the authenticated user's application.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID

from src.core.config import settings
from src.deps.auth import get_current_user
from src.domain.applications.repository import ApplicationRepository
from src.domain.jobs.repository import JobRepository
from src.domain.jobs.scoring.repository import ApplicationScoreRepository
from src.domain.jobs.scoring.schemas import JobScoreRead
from src.domain.jobs.scoring.service import JobScoringService
from src.domain.profile.repository import CandidateProfileRepository
from src.domain.resume.repository import ResumeRepository
from src.infrastructure.db.session import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/applications", tags=["application-scoring"])


def _build_scoring_service(db: Session) -> JobScoringService:
    llm_client = None
    if settings.groq_api_key:
        from src.integrations.groq.client import GroqClient

        llm_client = GroqClient(
            api_key=settings.groq_api_key,
            model=settings.groq_model,
        )

    return JobScoringService(
        application_repository=ApplicationRepository(db),
        job_repository=JobRepository(db),
        profile_repository=CandidateProfileRepository(db),
        resume_repository=ResumeRepository(db),
        score_repository=ApplicationScoreRepository(db),
        llm_client=llm_client,
    )


@router.post("/{application_id}/score", response_model=JobScoreRead)
def score_application(
    application_id: UUID,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = _build_scoring_service(db)

    try:
        return service.score_application(
            application_id=application_id,
            user_id=current_user.id,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
