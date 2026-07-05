"""Generates a personalized monthly budget allocation."""
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.db import BudgetItem, Transaction, UserProfile


class BudgetAgent:
    """
    Allocates income across categories based on the user's actual profile
    (income, debts, savings goal) rather than a fixed 50/30/20 rule.
    """

    BASE_WEIGHTS = {
        "rent": 0.30,
        "groceries": 0.12,
        "utilities": 0.06,
        "transport": 0.08,
        "healthcare": 0.05,
        "dining_out": 0.05,
        "entertainment": 0.04,
        "shopping": 0.05,
        "subscriptions": 0.02,
        "other": 0.03,
    }

    def generate_budget(self, db: Session, profile: UserProfile, month: str = None) -> dict:
        month = month or datetime.now(UTC).strftime("%Y-%m")
        income = profile.monthly_income

        total_min_debt_payment = sum(d.min_payment for d in profile.debts) if profile.debts else 0.0
        savings_target = max(profile.savings_goal, income * 0.10)  # never recommend below 10%

        # Remaining income after mandatory debt payments and savings target
        discretionary_pool = max(income - total_min_debt_payment - savings_target, 0)

        categories = []
        base_total_weight = sum(self.BASE_WEIGHTS.values())

        for cat, weight in self.BASE_WEIGHTS.items():
            allocated = round(discretionary_pool * (weight / base_total_weight), 2)
            categories.append({
                "category": cat,
                "allocated": allocated,
                "spent": 0.0,
                "remaining": allocated,
                "percent_of_income": round((allocated / income) * 100, 1) if income else 0,
            })

        if total_min_debt_payment > 0:
            categories.append({
                "category": "debt_payment",
                "allocated": round(total_min_debt_payment, 2),
                "spent": 0.0,
                "remaining": round(total_min_debt_payment, 2),
                "percent_of_income": round((total_min_debt_payment / income) * 100, 1) if income else 0,
            })

        categories.append({
            "category": "savings",
            "allocated": round(savings_target, 2),
            "spent": 0.0,
            "remaining": round(savings_target, 2),
            "percent_of_income": round((savings_target / income) * 100, 1) if income else 0,
        })

        reasoning = (
            f"Income ₹{income:,.0f}/mo. Reserved ₹{total_min_debt_payment:,.0f} for minimum debt "
            f"payments and ₹{savings_target:,.0f} ({round(savings_target/income*100,1) if income else 0}%) "
            f"for savings before allocating the remaining ₹{discretionary_pool:,.0f} across lifestyle "
            f"categories, weighted toward essentials (rent, groceries, utilities)."
        )

        # Persist to DB
        db.query(BudgetItem).filter_by(profile_id=profile.id, month=month).delete()
        for c in categories:
            db.add(BudgetItem(
                profile_id=profile.id, category=c["category"],
                allocated=c["allocated"], spent=0.0, month=month,
            ))
        db.commit()

        return {
            "user_id": profile.user_id,
            "month": month,
            "total_income": income,
            "categories": categories,
            "reasoning": reasoning,
        }

    def suggest_budget(self, db: Session, profile: UserProfile) -> dict:
        """
        Suggests a budget that blends the income-based starter allocation with
        the user's actual historical spending, category by category. Categories
        with enough logged history get a data-driven number (average monthly
        spend + a 10% buffer); categories with no history yet fall back to the
        income-based estimate. As the user logs more expenses, more categories
        graduate from "estimate" to "your spending history".
        """
        income = profile.monthly_income
        total_min_debt_payment = sum(d.min_payment for d in profile.debts) if profile.debts else 0.0
        savings_target = max(profile.savings_goal, income * 0.10)
        discretionary_pool = max(income - total_min_debt_payment - savings_target, 0)

        transactions = db.query(Transaction).filter_by(profile_id=profile.id).all()
        months_seen = {t.created_at.strftime("%Y-%m") for t in transactions}
        num_months = max(len(months_seen), 1)

        historical_totals: dict[str, float] = {}
        for t in transactions:
            historical_totals[t.category] = historical_totals.get(t.category, 0.0) + t.amount
        historical_avg = {cat: total / num_months for cat, total in historical_totals.items()}

        lifestyle_categories = (set(self.BASE_WEIGHTS.keys()) | set(historical_avg.keys())) - {
            "debt_payment", "savings",
        }

        base_total_weight = sum(self.BASE_WEIGHTS.values())
        raw_amounts: dict[str, float] = {}
        sources: dict[str, str] = {}

        for cat in lifestyle_categories:
            avg = historical_avg.get(cat, 0.0)
            if avg > 0:
                raw_amounts[cat] = avg * 1.10  # 10% buffer over your actual average
                sources[cat] = "your spending history"
            else:
                weight = self.BASE_WEIGHTS.get(cat, 0.03)
                raw_amounts[cat] = discretionary_pool * (weight / base_total_weight)
                sources[cat] = "income-based estimate"

        raw_total = sum(raw_amounts.values()) or 1.0
        scale = discretionary_pool / raw_total

        categories = []
        for cat, amount in raw_amounts.items():
            scaled = round(amount * scale, 2)
            categories.append({
                "category": cat,
                "suggested_allocated": scaled,
                "percent_of_income": round((scaled / income) * 100, 1) if income else 0,
                "based_on": sources[cat],
            })

        if total_min_debt_payment > 0:
            categories.append({
                "category": "debt_payment",
                "suggested_allocated": round(total_min_debt_payment, 2),
                "percent_of_income": round((total_min_debt_payment / income) * 100, 1) if income else 0,
                "based_on": "your debt obligations",
            })

        categories.append({
            "category": "savings",
            "suggested_allocated": round(savings_target, 2),
            "percent_of_income": round((savings_target / income) * 100, 1) if income else 0,
            "based_on": "your savings goal",
        })

        historical_count = sum(1 for s in sources.values() if s == "your spending history")

        if historical_count == 0:
            personalization_level = "starter"
            reasoning = (
                f"You don't have any logged expenses yet, so this is a starter budget based on your "
                f"income (₹{income:,.0f}), savings goal, and debts. Log a few expenses and check back "
                f"— the suggestion will refine itself to match your real spending."
            )
        elif historical_count < len(lifestyle_categories):
            personalization_level = "partially_personalized"
            reasoning = (
                f"Based on {num_months} month(s) of activity, {historical_count} "
                f"categor{'y' if historical_count == 1 else 'ies'} now reflect your real average "
                f"spending (with a 10% buffer). The rest are still starter estimates until you log "
                f"more expenses in those areas."
            )
        else:
            personalization_level = "personalized"
            reasoning = (
                f"This suggestion is fully based on your actual spending over the last {num_months} "
                f"month(s), with a 10% buffer added to each category so you have some room to breathe."
            )

        return {
            "user_id": profile.user_id,
            "month": datetime.now(UTC).strftime("%Y-%m"),
            "total_income": income,
            "categories": categories,
            "personalization_level": personalization_level,
            "reasoning": reasoning,
        }

