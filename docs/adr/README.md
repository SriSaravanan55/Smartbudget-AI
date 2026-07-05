# Architecture Decision Records

This directory records significant architectural decisions and the reasoning
behind them, so future contributors (including future-you) understand *why*
the code looks the way it does, not just *what* it does.

| ADR | Title | Status |
|---|---|---|
| [0001](0001-multi-agent-orchestration.md) | Multi-agent orchestration instead of one monolithic service | Accepted |
| [0002](0002-jwt-authentication.md) | JWT bearer authentication, user identity derived server-side | Accepted |
| [0003](0003-sqlite-with-postgres-migration-path.md) | SQLite for development, Postgres-ready via `DATABASE_URL` | Accepted |
