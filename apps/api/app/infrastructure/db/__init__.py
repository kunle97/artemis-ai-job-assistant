"""
Database initialization module.

Imports all models so SQLAlchemy metadata is aware of them.
This is important for table creation and future migrations.
"""

from app.domains.auth.models import User
from app.domains.profile.models import CandidateProfile

# IMPORTANT: keep these imports so models are registered