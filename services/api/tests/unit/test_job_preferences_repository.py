"""Unit tests for the job preferences repository."""

from __future__ import annotations

import uuid

from src.domain.auth.models import User
from src.domain.jobs.repository import JobPreferencesRepository
from src.domain.jobs.schemas import JobPreferencesSchema


def test_job_preferences_repository_creates_preferences_for_user(db_session):
    user = User(email=f"prefs-{uuid.uuid4().hex}@example.com", password="secret")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    repository = JobPreferencesRepository(db_session)

    payload = JobPreferencesSchema(
        target_titles=["Software Engineer", "Backend Engineer"],
        positive_keywords=["python", "fastapi"],
        negative_keywords=["ios"],
        locations=["Remote", "New York, NY"],
        remote_only=True,
        salary_min=150000,
        enabled_sources=["greenhouse", "lever"],
    )

    preferences = repository.upsert(user.id, payload)

    assert preferences.user_id == user.id
    assert preferences.target_titles == ["Software Engineer", "Backend Engineer"]
    assert preferences.positive_keywords == ["python", "fastapi"]
    assert preferences.negative_keywords == ["ios"]
    assert preferences.locations == ["Remote", "New York, NY"]
    assert preferences.remote_only is True
    assert preferences.salary_min == 150000
    assert preferences.enabled_sources == ["greenhouse", "lever"]


def test_job_preferences_repository_upsert_updates_existing_preferences(db_session):
    user = User(email=f"prefs-{uuid.uuid4().hex}@example.com", password="secret")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    repository = JobPreferencesRepository(db_session)

    original = repository.upsert(
        user.id,
        JobPreferencesSchema(
            target_titles=["Software Engineer"],
            positive_keywords=["python"],
            negative_keywords=[],
            locations=["Remote"],
            remote_only=False,
            salary_min=120000,
            enabled_sources=["greenhouse"],
        ),
    )

    updated = repository.upsert(
        user.id,
        JobPreferencesSchema(
            target_titles=["Senior Backend Engineer"],
            positive_keywords=["python", "postgres"],
            negative_keywords=["php"],
            locations=["Remote", "Boston, MA"],
            remote_only=True,
            salary_min=160000,
            enabled_sources=["greenhouse", "ashby"],
        ),
    )

    fetched = repository.get_by_user_id(user.id)

    assert updated.id == original.id
    assert fetched is not None
    assert fetched.target_titles == ["Senior Backend Engineer"]
    assert fetched.positive_keywords == ["python", "postgres"]
    assert fetched.negative_keywords == ["php"]
    assert fetched.locations == ["Remote", "Boston, MA"]
    assert fetched.remote_only is True
    assert fetched.salary_min == 160000
    assert fetched.enabled_sources == ["greenhouse", "ashby"]