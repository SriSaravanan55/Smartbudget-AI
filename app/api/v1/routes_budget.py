"""Budget, health-score, and report endpoints. All protected by auth and
scoped to the authenticated user."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db import User, get_db
from app.models import BudgetOut, HealthScoreOut, ReportOut, SuggestedBudgetOut
from app.orchestrator import Orchestrator

router = APIRouter(tags=["budget"])
orchestrator = Orchestrator()


@router.get("/budget", response_model=BudgetOut)
def get_budget(
    month: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return orchestrator.get_budget(db, current_user.user_id, month)


@router.get("/budget/suggested", response_model=SuggestedBudgetOut)
def get_suggested_budget(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """A smart budget suggestion: starts as an income-based estimate and
    refines category by category as the user logs real spending history."""
    return orchestrator.get_suggested_budget(db, current_user.user_id)


@router.post("/budget/apply-suggested", response_model=BudgetOut)
def apply_suggested_budget(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Replace this month's budget allocations with the current suggestion."""
    return orchestrator.apply_suggested_budget(db, current_user.user_id)


@router.get("/health-score", response_model=HealthScoreOut)
def get_health_score(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return orchestrator.get_health_score(db, current_user.user_id)


@router.get("/report", response_model=ReportOut)
def get_report(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return orchestrator.get_full_report(db, current_user.user_id)

