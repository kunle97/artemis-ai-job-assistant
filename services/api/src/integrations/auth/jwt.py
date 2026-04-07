# JWT token utilities for Artemis authentication.

from datetime import datetime, timedelta, timezone
from jose import jwt

from src.core.config import settings

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours


def create_access_token(subject: str) -> str:
    """Create a signed JWT with the given subject (user_id)."""
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": subject, "exp": expire}
    return jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)
