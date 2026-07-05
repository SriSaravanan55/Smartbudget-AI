"""Database models and session management for SmartBudget AI."""
from datetime import UTC, datetime

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, create_engine
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

from app.core.config import settings

engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class User(Base):
    """Auth identity. One User has exactly one UserProfile (financial data)."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, unique=True, index=True, nullable=False)  # public-facing username
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))

    profile = relationship("UserProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")


class UserProfile(Base):
    __tablename__ = "user_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.user_id"), unique=True, index=True, nullable=False)
    monthly_income = Column(Float, default=0.0)
    current_balance = Column(Float, default=0.0)  # income remaining unspent this month
    risk_tolerance = Column(String, default="moderate")  # low / moderate / high
    savings_goal = Column(Float, default=0.0)
    emergency_fund_target = Column(Float, default=0.0)
    emergency_fund_current = Column(Float, default=0.0)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))

    user = relationship("User", back_populates="profile")
    debts = relationship("Debt", back_populates="profile", cascade="all, delete-orphan")
    transactions = relationship("Transaction", back_populates="profile", cascade="all, delete-orphan")
    budget_items = relationship("BudgetItem", back_populates="profile", cascade="all, delete-orphan")


class Debt(Base):
    __tablename__ = "debts"

    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(Integer, ForeignKey("user_profiles.id"))
    name = Column(String)
    balance = Column(Float)
    interest_rate = Column(Float)  # annual %
    min_payment = Column(Float)

    profile = relationship("UserProfile", back_populates="debts")


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(Integer, ForeignKey("user_profiles.id"))
    raw_text = Column(String)
    category = Column(String)
    amount = Column(Float)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))

    profile = relationship("UserProfile", back_populates="transactions")


class BudgetItem(Base):
    __tablename__ = "budget_items"

    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(Integer, ForeignKey("user_profiles.id"))
    category = Column(String)
    allocated = Column(Float)
    spent = Column(Float, default=0.0)
    month = Column(String)  # e.g. "2026-07"

    profile = relationship("UserProfile", back_populates="budget_items")


def init_db():
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
