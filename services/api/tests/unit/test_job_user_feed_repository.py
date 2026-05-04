"""Unit tests for the job user feed repository."""

from src.domain.auth.models import User
from src.domain.jobs.models import Job, JobFeedStatus
from src.domain.jobs.repository import JobUserFeedRepository


def test_job_user_feed_repository_get_or_create_is_idempotent(db_session):
    user = User(
        email="feed-user@example.com",
        password="hashed",
        first_name="Feed",
        last_name="User",
    )
    job = Job(
        source="greenhouse",
        source_job_id="job-1",
        title="Backend Engineer",
        company_name="Acme",
        apply_url="https://example.com/jobs/1",
        is_active=True,
    )
    db_session.add(user)
    db_session.add(job)
    db_session.commit()

    repository = JobUserFeedRepository(db_session)

    first, first_created = repository.get_or_create(user.id, job.id)
    second, second_created = repository.get_or_create(user.id, job.id)

    assert first_created is True
    assert second_created is False
    assert first.id == second.id


def test_job_user_feed_repository_updates_status_and_lists_for_user(db_session):
    user = User(
        email="saved-user@example.com",
        password="hashed",
        first_name="Saved",
        last_name="User",
    )
    job = Job(
        source="greenhouse",
        source_job_id="job-2",
        title="Staff Engineer",
        company_name="Acme",
        apply_url="https://example.com/jobs/2",
        is_active=True,
    )
    db_session.add(user)
    db_session.add(job)
    db_session.commit()

    repository = JobUserFeedRepository(db_session)
    link, _ = repository.get_or_create(user.id, job.id)

    updated = repository.update_status(user.id, job.id, JobFeedStatus.SAVED)
    saved_links = repository.list_for_user(user.id, status=JobFeedStatus.SAVED)

    assert updated is not None
    assert updated.status == JobFeedStatus.SAVED
    assert len(saved_links) == 1
    assert saved_links[0].id == link.id