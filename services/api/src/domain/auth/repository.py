"""
Auth repository.
"""

from sqlalchemy.orm import Session

from src.domain.auth.models import RevokedToken, User


class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_email(self, email: str):
        return self.db.query(User).filter(User.email == email).first()

    def get_by_id(self, user_id):
        return self.db.query(User).filter(User.id == user_id).first()

    def create(self, **user_data):
        user = User(**user_data)
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def revoke_token(self, jti: str) -> RevokedToken:
        revoked = RevokedToken(jti=jti)
        self.db.add(revoked)
        self.db.commit()
        self.db.refresh(revoked)
        return revoked

    def is_token_revoked(self, jti: str) -> bool:
        return self.db.query(RevokedToken).filter(RevokedToken.jti == jti).first() is not None