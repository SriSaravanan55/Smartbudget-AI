"""Computes savings progress and a debt repayment strategy."""
from app.db import UserProfile


class DebtSavingsAgent:
    def savings_progress(self, profile: UserProfile) -> dict:
        target = profile.emergency_fund_target
        current = profile.emergency_fund_current
        pct = round((current / target) * 100, 1) if target else 0.0
        months_to_goal = None
        monthly_contribution = max(profile.savings_goal, 0)
        if monthly_contribution > 0 and target > current:
            months_to_goal = round((target - current) / monthly_contribution, 1)

        return {
            "emergency_fund_target": target,
            "emergency_fund_current": current,
            "percent_complete": pct,
            "estimated_months_to_goal": months_to_goal,
        }

    def debt_plan(self, profile: UserProfile, strategy: str = "avalanche") -> dict:
        """
        strategy: 'avalanche' (highest interest first — saves most money) or
                  'snowball' (smallest balance first — best for motivation).
        """
        debts = profile.debts
        if not debts:
            return {"strategy": strategy, "order": [], "total_debt": 0.0, "note": "No debts on file."}

        if strategy == "avalanche":
            ordered = sorted(debts, key=lambda d: -d.interest_rate)
        else:
            ordered = sorted(debts, key=lambda d: d.balance)

        total_debt = sum(d.balance for d in debts)
        order = [
            {"name": d.name, "balance": d.balance, "interest_rate": d.interest_rate, "min_payment": d.min_payment}
            for d in ordered
        ]

        return {
            "strategy": strategy,
            "order": order,
            "total_debt": round(total_debt, 2),
            "note": (
                "Avalanche pays off the highest-interest debt first to minimize total interest paid."
                if strategy == "avalanche"
                else "Snowball pays off the smallest balance first for quick psychological wins."
            ),
        }
