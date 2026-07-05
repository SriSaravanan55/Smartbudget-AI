"""Profile endpoint. All routes here require a valid access token, and
always operate on the authenticated user's own data -- there is no way to
pass someone else's user_id in the request."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db import User, get_db
from app.models import ProfileIn
from app.orchestrator import Orchestrator

router = APIRouter(prefix="/profile", tags=["profile"])
orchestrator = Orchestrator()


@router.post("", status_code=200)
def create_or_update_profile(
    data: ProfileIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    profile = orchestrator.create_or_update_profile(db, current_user.user_id, data)
    return {"status": "ok", "user_id": profile.user_id}
