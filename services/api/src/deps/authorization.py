"""
Authorization helpers.

Provides reusable authorization checks for resource ownership.
"""

from fastapi import HTTPException


def require_self_access(current_user_id, target_user_id):
    """
    Ensure the authenticated user is only accessing their own resources.
    """
    if str(current_user_id) != str(target_user_id):
        raise HTTPException(
            status_code=403,
            detail="You are not authorized to access this resource.",
        )