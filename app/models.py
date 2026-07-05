"""Pydantic schemas for API requests/responses."""

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class UserRegisterIn(BaseModel):
    user_id: str = Field(min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class UserLoginIn(BaseModel):
    email: EmailStr
    password: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str


class DebtIn(BaseModel):
    name: str
    balance: float
    interest_rate: float
    min_payment: float


class ProfileIn(BaseModel):
    monthly_income: float = Field(gt=0)
    risk_tolerance: str = Field(default="moderate", pattern="^(low|moderate|high)$")
    savings_goal: float = Field(default=0.0, ge=0)
    emergency_fund_target: float = Field(default=0.0, ge=0)
    emergency_fund_current: float = Field(default=0.0, ge=0)
    debts: list[DebtIn] = []


class ExpenseIn(BaseModel):
    text: str = Field(min_length=1, max_length=500)  # natural language, e.g. "I spent ₹500 on groceries"


class ExpenseOut(BaseModel):
    category: str
    amount: float
    remaining_in_category: float | None = None
    current_balance: float
    message: str


class TransactionOut(BaseModel):
    id: int
    category: str
    amount: float
    description: str
    created_at: datetime
    month: str


class ExpenseHistoryOut(BaseModel):
    user_id: str
    month: str  # a specific "YYYY-MM", or "all"
    total_spent: float
    current_balance: float
    transactions: list[TransactionOut]


class BudgetCategory(BaseModel):
    category: str
    allocated: float
    spent: float
    remaining: float
    percent_of_income: float


class BudgetOut(BaseModel):
    user_id: str
    month: str
    total_income: float
    current_balance: float
    categories: list[BudgetCategory]
    reasoning: str


class SuggestedBudgetCategory(BaseModel):
    category: str
    suggested_allocated: float
    percent_of_income: float
    based_on: str  # "your spending history" | "income-based estimate" | ...


class SuggestedBudgetOut(BaseModel):
    user_id: str
    month: str
    total_income: float
    categories: list[SuggestedBudgetCategory]
    personalization_level: str  # "starter" | "partially_personalized" | "personalized"
    reasoning: str


class HealthScoreOut(BaseModel):
    user_id: str
    score: int  # 0-100
    breakdown: dict
    summary: str


class ReportOut(BaseModel):
    user_id: str
    month: str
    budget: BudgetOut
    health_score: HealthScoreOut
    savings_progress: dict
    debt_plan: dict
    insights: list[str]
    action_items: list[str]

