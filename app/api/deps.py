"""Reusable FastAPI dependencies: DB session and current-user resolution."""
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.exceptions import AuthError
from app.core.security import decode_access_token
from app.db import User, get_db

# tokenUrl is just for the OpenAPI docs "Authorize" button; the actual login
# endpoint accepts JSON (email/password), not form data.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


def get_current_user(
    token: str | None = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    if not token:
        raise AuthError("Not authenticated. Include 'Authorization: Bearer <token>'.")

    user_id = decode_access_token(token)
    if not user_id:
        raise AuthError("Invalid or expired token.")

    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise AuthError("User no longer exists.")
    if not user.is_active:
        raise AuthError("This account has been deactivated.")

    return user
