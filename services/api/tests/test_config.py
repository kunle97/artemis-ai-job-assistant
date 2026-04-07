"""
Test configuration helpers.

Provides a separate SQLite database URL and other helpers used only in tests.
"""

from pathlib import Path


TEST_DB_PATH = Path("tests/test_artemis.db")
TEST_DATABASE_URL = f"sqlite:///{TEST_DB_PATH}"