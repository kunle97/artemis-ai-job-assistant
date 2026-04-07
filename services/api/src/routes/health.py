"""
Health API routes.

Simple health check endpoints for the Artemis API.
"""

from fastapi import APIRouter

router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
def health_check():
    return {"status": "ok"}