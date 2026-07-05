"""Expense logging endpoint. Protected by auth; always logs against the
authenticated user's own profile."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db import User, get_db
from app.models import ExpenseHistoryOut, ExpenseIn, ExpenseOut
from app.orchestrator import Orchestrator

router = APIRouter(prefix="/expense", tags=["expense"])
orchestrator = Orchestrator()


@router.post("", response_model=ExpenseOut)
def log_expense(
    data: ExpenseIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return orchestrator.log_expense(db, current_user.user_id, data.text)


@router.get("/history", response_model=ExpenseHistoryOut)
def get_expense_history(
    month: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List past transactions. Pass ?month=YYYY-MM to filter to one month,
    or omit it to see the full all-time history."""
    return orchestrator.get_expense_history(db, current_user.user_id, month)

