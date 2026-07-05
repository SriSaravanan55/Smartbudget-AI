"""Compiles output from all agents into a single monthly report."""
from app.llm import call_llm, llm_available


class ReportAgent:
    def compile_report(
        self, user_id: str, month: str, budget: dict, health_score: dict,
        savings_progress: dict, debt_plan: dict,
    ) -> dict:
        insights, action_items = self._generate_insights(budget, health_score, savings_progress, debt_plan)

        return {
            "user_id": user_id,
            "month": month,
            "budget": budget,
            "health_score": health_score,
            "savings_progress": savings_progress,
            "debt_plan": debt_plan,
            "insights": insights,
            "action_items": action_items,
        }

    def _generate_insights(self, budget, health_score, savings_progress, debt_plan) -> tuple[list, list]:
        if llm_available():
            try:
                return self._llm_insights(budget, health_score, savings_progress, debt_plan)
            except Exception:
                pass
        return self._rule_based_insights(budget, health_score, savings_progress, debt_plan)

    def _llm_insights(self, budget, health_score, savings_progress, debt_plan):
        system = (
            "You are a financial report writer. Given budget, health score, savings, and debt "
            "data as JSON, produce exactly: {\"insights\": [3 short strings], "
            "\"action_items\": [3 short imperative strings]}. Be specific, reference actual numbers."
        )
        prompt = (
            f"Budget: {budget}\nHealth score: {health_score}\n"
            f"Savings progress: {savings_progress}\nDebt plan: {debt_plan}"
        )
        import json
        raw = call_llm(system + "\nRespond ONLY with JSON.", prompt, max_tokens=400)
        cleaned = raw.strip().strip("`")
        if cleaned.startswith("json"):
            cleaned = cleaned[4:].strip()
        result = json.loads(cleaned)
        return result["insights"], result["action_items"]

    def _rule_based_insights(self, budget, health_score, savings_progress, debt_plan) -> tuple[list, list]:
        insights = []
        actions = []

        breakdown = health_score["breakdown"]
        lowest_area = min(breakdown, key=breakdown.get)
        insights.append(f"Your lowest-scoring area is {lowest_area.replace('_', ' ')}.")

        if savings_progress["percent_complete"] < 100:
            insights.append(
                f"Emergency fund is at {savings_progress['percent_complete']}% of target."
            )
            actions.append("Increase automated monthly transfer to your emergency fund.")

        if debt_plan["total_debt"] > 0:
            top_debt = debt_plan["order"][0]
            insights.append(
                f"Highest-priority debt under your {debt_plan['strategy']} strategy is "
                f"{top_debt['name']} at {top_debt['interest_rate']}% interest."
            )
            actions.append(f"Direct any extra payment toward {top_debt['name']} this month.")

        insights.append(f"Overall financial health score: {health_score['score']}/100.")
        actions.append("Review category spending against allocation weekly, not just monthly.")

        return insights[:3], actions[:3]
