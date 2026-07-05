"""Authentication business logic: registration, login, token issuance."""
import logging

from sqlalchemy.orm import Session

from app.core.exceptions import AuthError, ConflictError
from app.core.security import create_access_token, hash_password, verify_password
from app.db import User
from app.models import TokenOut, UserLoginIn, UserRegisterIn

logger = logging.getLogger(__name__)


class AuthService:
    def register(self, db: Session, data: UserRegisterIn) -> TokenOut:
        existing = db.query(User).filter(
            (User.user_id == data.user_id) | (User.email == data.email)
        ).first()
        if existing:
            field = "user_id" if existing.user_id == data.user_id else "email"
            raise ConflictError(f"A user with this {field} already exists.")

        user = User(
            user_id=data.user_id,
            email=data.email,
            hashed_password=hash_password(data.password),
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        logger.info("New user registered: %s", user.user_id)
        token = create_access_token(subject=user.user_id)
        return TokenOut(access_token=token, user_id=user.user_id)

    def login(self, db: Session, data: UserLoginIn) -> TokenOut:
        user = db.query(User).filter(User.email == data.email).first()
        if not user or not verify_password(data.password, user.hashed_password):
            raise AuthError("Incorrect email or password.")
        if not user.is_active:
            raise AuthError("This account has been deactivated.")

        logger.info("User logged in: %s", user.user_id)
        token = create_access_token(subject=user.user_id)
        return TokenOut(access_token=token, user_id=user.user_id)
