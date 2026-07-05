# ADR 0003: SQLite for development, Postgres-ready via `DATABASE_URL`

## Status
Accepted

## Context
The app needs a relational store for users, profiles, debts, transactions,
and budget items, with real foreign keys and cascade deletes. For local
development and for running on a single grader/interviewer machine, a
zero-setup database is valuable. For actual production use, SQLite's
single-writer model and lack of network access are limiting.

## Decision
Use SQLAlchemy as the only data-access layer, with `DATABASE_URL` read from
config (`app/core/config.py`) rather than hardcoded. Default to
`sqlite:///./smartbudget.db` for local/dev/CI. Switching to Postgres in
production is a one-line environment variable change
(`postgresql://user:pass@host:5432/dbname`) plus adding `psycopg2-binary` to
`requirements.txt` — no application code changes, because no code depends on
SQLite-specific SQL.

## Consequences
- Tests run against an in-memory SQLite DB (`sqlite:///:memory:`) for speed
  and isolation, with `StaticPool` so the single in-memory DB is shared
  across the app's request threads within a test.
- `connect_args={"check_same_thread": False}` is applied only when the URL
  contains `sqlite`, so it's a no-op (and harmless) for Postgres.
- We deliberately did not adopt a migrations tool (e.g. Alembic) yet, since
  the schema is still small and actively changing; `Base.metadata.create_all`
  is sufficient for now. This should be revisited before the first real
  production deploy with existing user data, since `create_all` cannot alter
  existing tables.
