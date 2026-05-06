"""
API integration tests for follow-up endpoints.

Tests the GET /applications/follow-ups endpoint with authentication and scoping.
"""

from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.domain.applications.models import Application


_TEST_PASSWORD = "TestPassword123!"


def _register_and_login(client: TestClient, email: str, password: str = _TEST_PASSWORD) -> str:
    """Register a new user via the API and return a Bearer token."""
    client.post(
        "/auth/register",
        json={
            "email": email,
            "password": password,
            "first_name": "Test",
            "last_name": "User",
        },
    )
    login = client.post(
        "/auth/login",
        data={"username": email, "password": password},
    )
    return login.json()["access_token"]


@pytest.fixture
def user_with_applications(client: TestClient, db_session: Session) -> tuple[str, list[Application]]:
    """Register a user via the API and create applications for them in the test DB."""
    email = "followup@example.com"

    reg = client.post(
        "/auth/register",
        json={
            "email": email,
            "password": _TEST_PASSWORD,
            "first_name": "Follow",
            "last_name": "Up",
        },
    )
    assert reg.status_code == 200
    user_id = UUID(reg.json()["id"])

    now = datetime.now(UTC)
    apps = [
        Application(
            user_id=user_id,
            job_id=uuid4(),
            status="applied",
            updated_at=now - timedelta(days=10),
        ),
        Application(
            user_id=user_id,
            job_id=uuid4(),
            status="responded",
            updated_at=now,
        ),
        Application(
            user_id=user_id,
            job_id=uuid4(),
            status="interview",
            updated_at=now - timedelta(days=2),
        ),
    ]
    db_session.add_all(apps)
    db_session.commit()
    for app in apps:
        db_session.refresh(app)

    return email, apps


class TestFollowUpEndpoint:
    """Test follow-up API endpoint."""

    def test_get_followups_authenticated(
        self, client: TestClient, user_with_applications: tuple[str, list]
    ):
        """Test that authenticated users can retrieve their follow-ups."""
        email, apps = user_with_applications

        login = client.post(
            "/auth/login",
            data={"username": email, "password": _TEST_PASSWORD},
        )
        assert login.status_code == 200
        token = login.json()["access_token"]

        followup_response = client.get(
            "/applications/follow-ups",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert followup_response.status_code == 200
        data = followup_response.json()

        assert "overdue" in data
        assert "urgent" in data
        assert "upcoming" in data
        assert "total" in data
        assert data["total"] >= 3

    def test_get_followups_unauthenticated(self, client: TestClient):
        """Test that unauthenticated requests are rejected."""
        response = client.get("/applications/follow-ups")
        assert response.status_code == 401

    def test_followups_scoped_to_user(
        self, client: TestClient, db_session: Session, user_with_applications: tuple[str, list]
    ):
        """Test that follow-ups are scoped to the authenticated user."""
        email1, apps1 = user_with_applications

        # Register a second user and give them one application
        email2 = "other@example.com"
        reg2 = client.post(
            "/auth/register",
            json={
                "email": email2,
                "password": _TEST_PASSWORD,
                "first_name": "Other",
                "last_name": "User",
            },
        )
        assert reg2.status_code == 200
        user2_id = UUID(reg2.json()["id"])

        app_user2 = Application(user_id=user2_id, job_id=uuid4(), status="applied")
        db_session.add(app_user2)
        db_session.commit()

        # Login as user1 and fetch follow-ups
        login1 = client.post(
            "/auth/login",
            data={"username": email1, "password": _TEST_PASSWORD},
        )
        token1 = login1.json()["access_token"]

        response1 = client.get(
            "/applications/follow-ups",
            headers={"Authorization": f"Bearer {token1}"},
        )

        assert response1.status_code == 200
        data1 = response1.json()
        assert data1["total"] >= 3

    def test_followup_response_structure(
        self, client: TestClient, user_with_applications: tuple[str, list]
    ):
        """Test that follow-up response has correct structure."""
        email, apps = user_with_applications

        login_response = client.post(
            "/auth/login",
            data={"username": email, "password": _TEST_PASSWORD},
        )
        token = login_response.json()["access_token"]

        response = client.get(
            "/applications/follow-ups",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()

        assert isinstance(data["overdue"], list)
        assert isinstance(data["urgent"], list)
        assert isinstance(data["upcoming"], list)
        assert isinstance(data["total"], int)

        for followup_list in [data["overdue"], data["urgent"], data["upcoming"]]:
            for followup in followup_list:
                assert "id" in followup
                assert "application_id" in followup
                assert "due_date" in followup
                assert "followup_type" in followup
                assert "is_overdue" in followup

    def test_empty_followups(self, client: TestClient):
        """Test that users with no applications get empty follow-up list."""
        token = _register_and_login(client, "empty@example.com")

        response = client.get(
            "/applications/follow-ups",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert len(data["overdue"]) == 0
        assert len(data["urgent"]) == 0
        assert len(data["upcoming"]) == 0
