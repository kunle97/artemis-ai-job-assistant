"""
Base DB model class.

All SQLAlchemy models in Artemis should inherit from this.
Later we will import all domain models here so Alembic can detect them.
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass