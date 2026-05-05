"""Unit tests for ApplicationService status lifecycle defaults."""

from __future__ import annotations

import uuid
from types import SimpleNamespace
from unittest.mock import MagicMock

from src.domain.applications.constants import (
    APPLICATION_STATUS_NEEDS_REVIEW,
    APPLICATION_STATUS_QUEUED,
)
from src.domain.applications.schemas import ApplicationCreate
from src.domain.applications.service import ApplicationService


def _build_service(
    *,
    profile=None,
    resumes=None,
    selected_resume=None,
):
    repository = MagicMock()
    job_repository = MagicMock()
    profile_repository = MagicMock()
    resume_repository = MagicMock()

    job_repository.get_by_id.return_value = SimpleNamespace(id=uuid.uuid4())
    repository.get_by_user_and_job.return_value = None

    profile_repository.get_by_user_id.return_value = profile
    resume_repository.get_by_user_id.return_value = resumes or []
    resume_repository.get_by_id_and_user_id.return_value = selected_resume

    service = ApplicationService(
        repository=repository,
        job_repository=job_repository,
        profile_repository=profile_repository,
        resume_repository=resume_repository,
    )
    return service, repository


def test_create_application_ready_defaults_to_queued_status():
    user_id = uuid.uuid4()
    job_id = uuid.uuid4()

    profile = SimpleNamespace(auto_submit=False)
    resume = SimpleNamespace(id=uuid.uuid4())

    service, repository = _build_service(profile=profile, resumes=[resume])
    repository.create.return_value = SimpleNamespace(id=uuid.uuid4())

    service.create_application(user_id, ApplicationCreate(job_id=job_id, notes=None))

    assert repository.create.call_count == 1
    kwargs = repository.create.call_args.kwargs
    assert kwargs["status"] == APPLICATION_STATUS_QUEUED
    assert kwargs["is_ready_for_automation"] is True


def test_create_application_not_ready_defaults_to_needs_review_status():
    user_id = uuid.uuid4()
    job_id = uuid.uuid4()

    # No profile and no resume means readiness fails.
    service, repository = _build_service(profile=None, resumes=[])
    repository.create.return_value = SimpleNamespace(id=uuid.uuid4())

    service.create_application(user_id, ApplicationCreate(job_id=job_id, notes=None))

    kwargs = repository.create.call_args.kwargs
    assert kwargs["status"] == APPLICATION_STATUS_NEEDS_REVIEW
    assert kwargs["is_ready_for_automation"] is False
