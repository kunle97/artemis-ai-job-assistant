"""
Shared pytest fixtures.

Sets up a dedicated test database, overrides FastAPI dependencies,
and provides reusable API clients and factory helpers for tests.
"""

from pathlib import Path
import sys
import uuid

# Make the apps/api directory importable as the project root for tests.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.infrastructure.db.base import Base
from app.infrastructure.db.session import get_db
from app.main import app as fastapi_app
import app.infrastructure.db as db_models
from tests.test_config import TEST_DATABASE_URL, TEST_DB_PATH


engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    future=True,
)
TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


def override_get_db():
    """
    Override the production DB dependency with a test database session.
    """
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


fastapi_app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """
    Ensure the SQLite test DB file starts clean for the session.
    """
    if TEST_DB_PATH.exists():
        TEST_DB_PATH.unlink()

    yield

    if TEST_DB_PATH.exists():
        TEST_DB_PATH.unlink()


@pytest.fixture(autouse=True)
def reset_database():
    """
    Reset all tables before each test so tests stay isolated.
    """
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture()
def db_session():
    """
    Provide a fresh DB session for direct repository/service tests.
    """
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture()
def client():
    """
    Provide a FastAPI test client.
    """
    return TestClient(fastapi_app)


@pytest.fixture()
def sample_user_payload():
    """
    Return a unique user payload for each test.
    """
    unique_value = uuid.uuid4().hex[:8]
    return {
        "email": f"test-{unique_value}@example.com",
        "password": "password123",
        "full_name": "Test User",
    }