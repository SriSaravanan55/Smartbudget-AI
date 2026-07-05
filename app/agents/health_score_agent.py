"""Calculates a 0-100 financial health score from key ratios."""
from app.db import UserProfile


class HealthScoreAgent:
    def score(self, profile: UserProfile, budget: dict) -> dict:
        income = profile.monthly_income or 1  # avoid div by zero

        # 1. Savings rate (0-30 pts)
        savings_item = next((c for c in budget["categories"] if c["category"] == "savings"), None)
        savings_rate = (savings_item["allocated"] / income) if savings_item else 0
        savings_pts = min(savings_rate / 0.20, 1.0) * 30  # 20%+ savings rate = full points

        # 2. Debt-to-income ratio (0-25 pts) — lower is better
        total_debt_payment = sum(d.min_payment for d in profile.debts) if profile.debts else 0
        dti = total_debt_payment / income
        dti_pts = max(0, 1 - (dti / 0.36)) * 25  # 36%+ DTI = 0 points

        # 3. Emergency fund coverage (0-25 pts)
        ef_coverage = (
            profile.emergency_fund_current / profile.emergency_fund_target
            if profile.emergency_fund_target else 0
        )
        ef_pts = min(ef_coverage, 1.0) * 25

        # 4. Budget adherence (0-20 pts) — based on spent vs allocated across categories
        total_allocated = sum(c["allocated"] for c in budget["categories"])
        total_spent = sum(c["spent"] for c in budget["categories"])
        if total_allocated > 0:
            overspend_ratio = max(0, (total_spent - total_allocated) / total_allocated)
            adherence_pts = max(0, 1 - overspend_ratio) * 20
        else:
            adherence_pts = 20  # no data yet, don't penalize

        total_score = round(savings_pts + dti_pts + ef_pts + adherence_pts)

        breakdown = {
            "savings_rate_score": round(savings_pts, 1),
            "debt_to_income_score": round(dti_pts, 1),
            "emergency_fund_score": round(ef_pts, 1),
            "budget_adherence_score": round(adherence_pts, 1),
        }

        if total_score >= 80:
            summary = "Strong financial health. Keep up current habits."
        elif total_score >= 60:
            summary = "Good foundation with room to improve — check the lowest-scoring area below."
        elif total_score >= 40:
            summary = "Financial health needs attention. Focus on savings rate and debt reduction."
        else:
            summary = "Financial health is at risk. Prioritize an emergency fund and reducing high-interest debt."

        return {"user_id": profile.user_id, "score": total_score, "breakdown": breakdown, "summary": summary}
