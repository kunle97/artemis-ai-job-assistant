"""
Auth domain schemas.

Pydantic request/response models related to users in the Artemis system.
"""

from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    email: EmailStr
    password: str | None = None
    full_name: str | None = None


class UserRead(BaseModel):
    id: UUID
    email: EmailStr
    full_name: str | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True