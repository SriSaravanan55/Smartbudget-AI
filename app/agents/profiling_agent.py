"""Builds and updates the user's financial profile."""
from sqlalchemy.orm import Session

from app.db import Debt, UserProfile
from app.models import ProfileIn


class ProfilingAgent:
    def upsert_profile(self, db: Session, user_id: str, data: ProfileIn) -> UserProfile:
        profile = db.query(UserProfile).filter_by(user_id=user_id).first()
        if profile is None:
            profile = UserProfile(user_id=user_id)
            db.add(profile)

        profile.monthly_income = data.monthly_income
        profile.current_balance = data.monthly_income  # fresh month starts with the full income
        profile.risk_tolerance = data.risk_tolerance
        profile.savings_goal = data.savings_goal
        profile.emergency_fund_target = data.emergency_fund_target
        profile.emergency_fund_current = data.emergency_fund_current

        db.commit()
        db.refresh(profile)

        # Replace debts wholesale for simplicity
        db.query(Debt).filter_by(profile_id=profile.id).delete()
        for d in data.debts:
            db.add(Debt(
                profile_id=profile.id,
                name=d.name,
                balance=d.balance,
                interest_rate=d.interest_rate,
                min_payment=d.min_payment,
            ))
        db.commit()
        db.refresh(profile)
        return profile

    def get_profile(self, db: Session, user_id: str) -> UserProfile | None:
        return db.query(UserProfile).filter_by(user_id=user_id).first()
