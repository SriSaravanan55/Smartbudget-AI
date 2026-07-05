"""Coordinates all agents to fulfill a request. Central entry point for agent logic."""
import logging
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.agents.budget_agent import BudgetAgent
from app.agents.categorization_agent import CategorizationAgent
from app.agents.debt_savings_agent import DebtSavingsAgent
from app.agents.health_score_agent import HealthScoreAgent
from app.agents.investment_agent import InvestmentAgent
from app.agents.profiling_agent import ProfilingAgent
from app.agents.report_agent import ReportAgent
from app.core.exceptions import NotFoundError
from app.db import BudgetItem, Transaction, UserProfile
from app.models import ProfileIn

logger = logging.getLogger(__name__)


class Orchestrator:
    def __init__(self):
        self.profiling = ProfilingAgent()
        self.categorization = CategorizationAgent()
        self.budget = BudgetAgent()
        self.debt_savings = DebtSavingsAgent()
        self.investment = InvestmentAgent()
        self.health = HealthScoreAgent()
        self.report = ReportAgent()

    def _require_profile(self, db: Session, user_id: str) -> UserProfile:
        profile = self.profiling.get_profile(db, user_id)
        if not profile:
            raise NotFoundError(
                f"No financial profile found for '{user_id}'. Create one via POST /api/v1/profile first."
            )
        return profile

    def create_or_update_profile(self, db: Session, user_id: str, data: ProfileIn) -> UserProfile:
        profile = self.profiling.upsert_profile(db, user_id, data)
        # Regenerate budget whenever profile changes
        self.budget.generate_budget(db, profile)
        logger.info("Profile + budget updated for user_id=%s", user_id)
        return profile

    def log_expense(self, db: Session, user_id: str, text: str) -> dict:
        profile = self._require_profile(db, user_id)

        result = self.categorization.categorize(text)
        category, amount = result["category"], result["amount"]

        db.add(Transaction(profile_id=profile.id, raw_text=text, category=category, amount=amount))

        month = datetime.now(UTC).strftime("%Y-%m")
        item = db.query(BudgetItem).filter_by(profile_id=profile.id, category=category, month=month).first()
        remaining = None
        if item:
            item.spent += amount
            remaining = round(item.allocated - item.spent, 2)

        profile.current_balance = round((profile.current_balance or 0.0) - amount, 2)
        db.commit()

        logger.info("Expense logged for user_id=%s: %s ₹%.2f", user_id, category, amount)

        message = f"Logged ₹{amount:,.0f} under '{category}'."
        if remaining is not None:
            message += f" ₹{remaining:,.0f} remaining in this category for {month}."
        message += f" Overall balance: ₹{profile.current_balance:,.0f}."

        return {
            "category": category,
            "amount": amount,
            "remaining_in_category": remaining,
            "current_balance": profile.current_balance,
            "message": message,
        }

    def get_expense_history(self, db: Session, user_id: str, month: str | None = None) -> dict:
        profile = self._require_profile(db, user_id)

        all_tx = (
            db.query(Transaction)
            .filter_by(profile_id=profile.id)
            .order_by(Transaction.created_at.desc())
            .all()
        )
        if month:
            filtered = [t for t in all_tx if t.created_at.strftime("%Y-%m") == month]
        else:
            filtered = all_tx

        total_spent = sum(t.amount for t in filtered)

        return {
            "user_id": user_id,
            "month": month or "all",
            "total_spent": round(total_spent, 2),
            "current_balance": round(profile.current_balance or 0.0, 2),
            "transactions": [
                {
                    "id": t.id,
                    "category": t.category,
                    "amount": t.amount,
                    "description": t.raw_text,
                    "created_at": t.created_at,
                    "month": t.created_at.strftime("%Y-%m"),
                }
                for t in filtered
            ],
        }

    def get_budget(self, db: Session, user_id: str, month: str = None) -> dict:
        profile = self._require_profile(db, user_id)
        month = month or datetime.now(UTC).strftime("%Y-%m")

        items = db.query(BudgetItem).filter_by(profile_id=profile.id, month=month).all()
        if not items:
            result = self.budget.generate_budget(db, profile, month)
            result["current_balance"] = round(profile.current_balance or 0.0, 2)
            return result

        categories = [{
            "category": i.category,
            "allocated": i.allocated,
            "spent": i.spent,
            "remaining": round(i.allocated - i.spent, 2),
            "percent_of_income": round((i.allocated / profile.monthly_income) * 100, 1) if profile.monthly_income else 0,
        } for i in items]

        return {
            "user_id": user_id,
            "month": month,
            "total_income": profile.monthly_income,
            "current_balance": round(profile.current_balance or 0.0, 2),
            "categories": categories,
            "reasoning": "Existing budget for this month.",
        }

    def get_suggested_budget(self, db: Session, user_id: str) -> dict:
        profile = self._require_profile(db, user_id)
        return self.budget.suggest_budget(db, profile)

    def apply_suggested_budget(self, db: Session, user_id: str) -> dict:
        profile = self._require_profile(db, user_id)
        suggestion = self.budget.suggest_budget(db, profile)
        month = datetime.now(UTC).strftime("%Y-%m")

        # Preserve amounts already spent this month per category; only the
        # envelopes (allocated amounts) are being reallocated, not the past.
        existing_spent = {
            item.category: item.spent
            for item in db.query(BudgetItem).filter_by(profile_id=profile.id, month=month).all()
        }

        db.query(BudgetItem).filter_by(profile_id=profile.id, month=month).delete()
        for c in suggestion["categories"]:
            db.add(BudgetItem(
                profile_id=profile.id,
                category=c["category"],
                allocated=c["suggested_allocated"],
                spent=existing_spent.get(c["category"], 0.0),
                month=month,
            ))
        db.commit()

        logger.info("Suggested budget applied for user_id=%s", user_id)
        return self.get_budget(db, user_id, month)

    def get_health_score(self, db: Session, user_id: str) -> dict:
        profile = self._require_profile(db, user_id)
        budget = self.get_budget(db, user_id)
        return self.health.score(profile, budget)

    def get_full_report(self, db: Session, user_id: str) -> dict:
        profile = self._require_profile(db, user_id)

        month = datetime.now(UTC).strftime("%Y-%m")
        budget = self.get_budget(db, user_id, month)
        health_score = self.health.score(profile, budget)
        savings_progress = self.debt_savings.savings_progress(profile)
        debt_plan = self.debt_savings.debt_plan(profile)

        return self.report.compile_report(
            user_id, month, budget, health_score, savings_progress, debt_plan
        )
