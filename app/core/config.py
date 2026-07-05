"""Centralized application configuration.

All environment-dependent values live here instead of being scattered as
os.getenv() calls across the codebase. Loads from environment variables or a
.env file.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # App
    app_name: str = "SmartBudget AI"
    environment: str = "development"  # development | production
    log_level: str = "INFO"

    # Database
    database_url: str = "sqlite:///./smartbudget.db"

    # Auth
    jwt_secret_key: str = "change-this-in-production-to-a-random-secret"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24  # 24 hours

    # LLM
    anthropic_api_key: str | None = None

    # CORS (for the Streamlit frontend / any browser client)
    cors_origins: list[str] = ["http://localhost:8501", "http://127.0.0.1:8501"]


settings = Settings()
