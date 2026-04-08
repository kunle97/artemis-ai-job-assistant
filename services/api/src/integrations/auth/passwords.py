"""
Password security helpers.

Handles password hashing and password verification for Artemis auth flows.
"""

from passlib.context import CryptContext


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """
    Hash a plaintext password for safe storage.
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plaintext password against a stored password hash.
    """
    return pwd_context.verify(plain_password, hashed_password)