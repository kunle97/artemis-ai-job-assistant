"""
Auth cleanup utilities.

Provides a function to purge expired rows from the revoked_tokens table.
Intended to be called from a scheduled job or a management script.
"""

import logging

from sqlalchemy.orm import Session

from src.domain.auth.repository import UserRepository

logger = logging.getLogger(__name__)


def purge_expired_revoked_tokens(db: Session) -> int:
    """Delete revoked_tokens rows whose token expiry has already passed.

    Returns the number of rows deleted.
    """
    logger.info("purge_expired_revoked_tokens: start")
    repo = UserRepository(db)
    deleted = repo.delete_expired_tokens()
    logger.info("purge_expired_revoked_tokens: deleted %d expired rows", deleted)
    return deleted
