"""
Authorization helpers.

Provides reusable authorization checks for resource ownership.
"""

import logging

from fastapi import HTTPException

logger = logging.getLogger(__name__)


def require_self_access(current_user_id, target_user_id):
    """
    Ensure the authenticated user is only accessing their own resources.
    """
    if str(current_user_id) != str(target_user_id):
        logger.warning(
            "require_self_access: forbidden access current_user=%s target_owner=%s",
            current_user_id,
            target_user_id,
        )
        raise HTTPException(
            status_code=403,
            detail="You are not authorized to access this resource.",
        )


def require_application_owner(application, current_user) -> None:
    """
    Verify the current user owns the given application.
    Raises 404 if the application is None, 403 if ownership fails.
    """
    if application is None:
        raise HTTPException(status_code=404, detail="Application not found.")
    require_self_access(current_user.id, application.user_id)


def require_resume_owner(resume, current_user) -> None:
    """
    Verify the current user owns the given resume.
    Raises 404 if the resume is None, 403 if ownership fails.
    """
    if resume is None:
        raise HTTPException(status_code=404, detail="Resume not found.")
    require_self_access(current_user.id, resume.user_id)