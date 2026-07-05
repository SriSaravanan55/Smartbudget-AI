"""Authentication endpoints: register and login."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import TokenOut, UserLoginIn, UserRegisterIn
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])
service = AuthService()


@router.post("/register", response_model=TokenOut, status_code=201)
def register(data: UserRegisterIn, db: Session = Depends(get_db)):
    """Create a new account and return an access token."""
    return service.register(db, data)


@router.post("/login", response_model=TokenOut)
def login(data: UserLoginIn, db: Session = Depends(get_db)):
    """Exchange email/password for an access token."""
    return service.login(db, data)
