# Architecture

## Overview

SmartBudget AI is a multi-agent personal finance advisor with a FastAPI backend
and a Streamlit frontend. Each domain concern (profiling, categorization,
budgeting, debt/savings, investment guidance, health scoring, reporting) is
owned by a dedicated agent; a thin `Orchestrator` coordinates them per request.
Authentication is a first-class concern, not bolted on — every data-bearing
endpoint resolves the caller from a JWT and operates only on that caller's own
data.

## System diagram

```
┌───────────────────────┐         ┌──────────────────────────────────────┐
│  Streamlit Frontend    │  HTTPS  │            FastAPI Backend            │
│  (frontend/app.py)     │────────▶│                                        │
│  - Login/Register UI   │  JWT    │  ┌──────────────────────────────────┐ │
│  - Profile/Budget/     │ Bearer  │  │  API layer (app/api/v1/*)         │ │
│    Expense/Report UI   │  token  │  │  routes_auth · routes_profile ·   │ │
└───────────────────────┘         │  │  routes_expense · routes_budget   │ │
                                    │  └───────────────┬────────────────────┘ │
                                    │                  ▼                      │
                                    │  ┌──────────────────────────────────┐ │
                                    │  │        Orchestrator               │ │
                                    │  └───────────────┬────────────────────┘ │
                                    │                  ▼                      │
                    ┌───────────────┴──────────────────────────────────────┐ │
                    │   Profiling │ Categorization │ Budget │ Debt/Savings   │ │
                    │   Investment │ Health Score │ Report      (agents)     │ │
                    └───────────────┬──────────────────────────────────────┘ │
                                    │                  │                      │
                                    ▼                  ▼                      │
                          ┌──────────────┐   ┌──────────────────┐             │
                          │  SQLAlchemy  │   │  ChromaDB (RAG,   │             │
                          │  (SQLite /   │   │  optional) for    │             │
                          │  Postgres)   │   │  investment tips  │             │
                          └──────────────┘   └──────────────────┘             │
                                    └──────────────────────────────────────────┘
```

## Request flow (example: logging an expense)

1. Streamlit sends `POST /api/v1/expense` with `Authorization: Bearer <jwt>`.
2. `app/api/deps.py::get_current_user` decodes the JWT, loads the `User` row,
   and rejects the request (401) if the token is missing, invalid, expired,
   or the account is deactivated.
3. `routes_expense.py` calls `Orchestrator.log_expense(db, current_user.user_id, text)`
   — the route handler never trusts a client-supplied `user_id`.
4. The orchestrator asks `CategorizationAgent` to parse the text (LLM if
   `ANTHROPIC_API_KEY` is set, else a rule-based keyword matcher).
5. The transaction is persisted and the matching `BudgetItem.spent` is updated.
6. A structured JSON response is returned; domain errors (e.g. "no profile
   yet") are raised as typed exceptions (`app/core/exceptions.py`) and
   translated to consistent HTTP responses by a global exception handler.

## Layering

| Layer | Location | Responsibility |
|---|---|---|
| API | `app/api/v1/*` | HTTP concerns only: request/response shapes, status codes, auth dependency wiring |
| Orchestration | `app/orchestrator.py` | Coordinates agents, enforces "profile must exist" invariants |
| Domain/Agents | `app/agents/*` | Business logic — budgeting rules, scoring formulas, categorization |
| Services | `app/services/*` | Cross-cutting business logic not tied to one agent (currently: auth) |
| Core | `app/core/*` | Config, security primitives, logging, exception types — no business logic |
| Persistence | `app/db.py` | SQLAlchemy models and session management |

This separation means, for example, the budget-allocation formula in
`BudgetAgent` can be unit-tested with a plain Python object and no HTTP layer
or database at all (see `tests/test_agents.py`).

## Security model

- Passwords are hashed with bcrypt (`passlib`), never stored or logged in
  plaintext.
- Access tokens are JWTs signed with `JWT_SECRET_KEY`, carrying the `user_id`
  as `sub` and an expiry (`exp`).
- Every profile/expense/budget/report endpoint requires a valid token and
  derives the acting user from it — there is no request parameter that lets
  one authenticated user address another user's data. This is verified by
  `tests/test_budget_and_reports.py::test_users_cannot_access_each_others_data`.
- CORS is restricted to the configured frontend origin(s) rather than `*`.

## Configuration

All environment-dependent values are centralized in `app/core/config.py`
(pydantic-settings) and loaded from environment variables or a `.env` file.
Nothing sensitive is hardcoded in application code — see `.env.example`.

## Deployment

`Dockerfile` builds the backend as a non-root user with a `/healthz` liveness
endpoint. `frontend/Dockerfile` builds the Streamlit UI similarly.
`docker-compose.yml` wires both together with a named volume for the SQLite
file. For real production use, swap `DATABASE_URL` to a managed Postgres
instance — no code changes are required (see ADR 0003).
