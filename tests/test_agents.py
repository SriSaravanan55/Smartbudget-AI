"""Unit tests for individual agents' business logic."""
from app.agents.categorization_agent import CategorizationAgent
from app.agents.debt_savings_agent import DebtSavingsAgent
from app.agents.health_score_agent import HealthScoreAgent


class FakeDebt:
    def __init__(self, name, balance, interest_rate, min_payment):
        self.name = name
        self.balance = balance
        self.interest_rate = interest_rate
        self.min_payment = min_payment


class FakeProfile:
    def __init__(self, monthly_income=60000, emergency_fund_target=180000,
                 emergency_fund_current=30000, savings_goal=8000, debts=None, user_id="testuser"):
        self.user_id = user_id
        self.monthly_income = monthly_income
        self.emergency_fund_target = emergency_fund_target
        self.emergency_fund_current = emergency_fund_current
        self.savings_goal = savings_goal
        self.debts = debts or []


def test_categorization_agent_rule_based_groceries():
    agent = CategorizationAgent()
    result = agent._categorize_rule_based("spent 500 on groceries today")
    assert result["category"] == "groceries"
    assert result["amount"] == 500.0


def test_categorization_agent_rule_based_transport():
    agent = CategorizationAgent()
    result = agent._categorize_rule_based("took an uber for 250")
    assert result["category"] == "transport"
    assert result["amount"] == 250.0


def test_categorization_agent_falls_back_to_other():
    agent = CategorizationAgent()
    result = agent._categorize_rule_based("bought something random for 99")
    assert result["category"] == "other"
    assert result["amount"] == 99.0


def test_categorization_agent_handles_no_amount():
    agent = CategorizationAgent()
    result = agent._categorize_rule_based("groceries")
    assert result["category"] == "groceries"
    assert result["amount"] == 0.0


def test_health_score_perfect_profile_scores_high():
    agent = HealthScoreAgent()
    profile = FakeProfile(
        monthly_income=100000, emergency_fund_target=100000,
        emergency_fund_current=100000, savings_goal=20000, debts=[],
    )
    budget = {
        "categories": [
            {"category": "savings", "allocated": 20000, "spent": 20000},
        ]
    }
    result = agent.score(profile, budget)
    assert result["score"] > 60


def test_health_score_no_emergency_fund_scores_lower():
    agent = HealthScoreAgent()
    good = FakeProfile(emergency_fund_current=180000, emergency_fund_target=180000)
    bad = FakeProfile(emergency_fund_current=0, emergency_fund_target=180000)
    budget = {"categories": []}

    good_score = agent.score(good, budget)["score"]
    bad_score = agent.score(bad, budget)["score"]
    assert good_score > bad_score


def test_debt_plan_avalanche_orders_by_highest_interest_first():
    agent = DebtSavingsAgent()
    profile = FakeProfile(debts=[
        FakeDebt("Credit Card", 50000, 24.0, 2000),
        FakeDebt("Education Loan", 200000, 9.5, 4000),
        FakeDebt("Personal Loan", 30000, 14.0, 1500),
    ])
    plan = agent.debt_plan(profile, strategy="avalanche")
    order = [d["name"] for d in plan["order"]]
    assert order == ["Credit Card", "Personal Loan", "Education Loan"]


def test_debt_plan_snowball_orders_by_smallest_balance_first():
    agent = DebtSavingsAgent()
    profile = FakeProfile(debts=[
        FakeDebt("Credit Card", 50000, 24.0, 2000),
        FakeDebt("Education Loan", 200000, 9.5, 4000),
        FakeDebt("Personal Loan", 30000, 14.0, 1500),
    ])
    plan = agent.debt_plan(profile, strategy="snowball")
    order = [d["name"] for d in plan["order"]]
    assert order == ["Personal Loan", "Credit Card", "Education Loan"]


def test_debt_plan_with_no_debts():
    agent = DebtSavingsAgent()
    profile = FakeProfile(debts=[])
    plan = agent.debt_plan(profile)
    assert plan["total_debt"] == 0.0
    assert plan["order"] == []


def test_savings_progress_calculates_percent_complete():
    agent = DebtSavingsAgent()
    profile = FakeProfile(emergency_fund_target=100000, emergency_fund_current=25000, savings_goal=5000)
    result = agent.savings_progress(profile)
    assert result["percent_complete"] == 25.0
    assert result["estimated_months_to_goal"] == 15.0
