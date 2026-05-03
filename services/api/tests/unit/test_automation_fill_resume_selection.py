"""
Automation fill resume selection tests.

Verifies application-scoped resume resolution uses application.resume_id.
"""

from types import SimpleNamespace
from uuid import uuid4

from src.domain.automation.fill.models import AutomationFillRequest
from src.domain.automation.fill.service import AutomationFillService


class _FakeApplicationRepository:
    def __init__(self, application):
        self._application = application

    def get_by_id(self, _application_id):
        return self._application


class _FakeResumeRepository:
    def __init__(self, resume):
        self._resume = resume

    def get_by_id_and_user_id(self, _resume_id, _user_id):
        return self._resume


def test_resolve_resume_file_path_uses_application_resume_id():
    user_id = uuid4()
    resume_id = uuid4()
    application_id = uuid4()

    fake_application = SimpleNamespace(id=application_id, user_id=user_id, resume_id=resume_id)
    fake_resume = SimpleNamespace(id=resume_id, file_path="s3://bucket/tailored-resume.pdf")

    service = AutomationFillService(
        planning_service=SimpleNamespace(),
        application_repository=_FakeApplicationRepository(fake_application),
        resume_repository=_FakeResumeRepository(fake_resume),
    )

    payload = AutomationFillRequest(
        application_url="https://example.com/apply",
        inspected_fields=[],
        application_id=application_id,
        resume_file_path="s3://bucket/ignored-resume.pdf",
    )

    resolved_path = service._resolve_resume_file_path(user_id=user_id, payload=payload)
    assert resolved_path == "s3://bucket/tailored-resume.pdf"


def test_resolve_resume_file_path_uses_payload_when_no_application_id():
    service = AutomationFillService(planning_service=SimpleNamespace())

    payload = AutomationFillRequest(
        application_url="https://example.com/apply",
        inspected_fields=[],
        resume_file_path="s3://bucket/direct-resume.pdf",
    )

    resolved_path = service._resolve_resume_file_path(user_id=uuid4(), payload=payload)
    assert resolved_path == "s3://bucket/direct-resume.pdf"
