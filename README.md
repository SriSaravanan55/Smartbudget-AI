# SmartBudget AI

A full-stack, multi-agent personal finance advisor. FastAPI backend with JWT auth,
a React (Vite) frontend, seven specialized agents coordinated by a central
orchestrator, structured logging, domain-level error handling, a pytest suite,
Docker, and CI.

## Architecture

```
                        ┌──────────────────────┐
                        │   React Frontend      │
                        │   (frontend/, Vite)   │
                        └───────────┬───────────┘
                                    │ HTTPS + JWT
                        ┌───────────▼───────────┐
                        │   FastAPI Gateway      │
                        │   /api/v1/*            │
                        │   (auth, CORS, logging,│
                        │    exception handling) │
                        └───────────┬───────────┘
                                    │
                        ┌───────────▼───────────┐
                        │     Orchestrator       │
                        └───────────┬───────────┘
           ┌───────────┬───────────┼───────────┬────────────┬───────────┐
           ▼           ▼           ▼           ▼            ▼           ▼
    ┌───────────┐┌───────────┐┌──────────┐┌──────────┐┌───────────┐┌──────────┐
    │ Profiling ││Categoriza-││ Budget   ││ Savings/ ││Investment ││  Health  │
    │  Agent    ││ tion Agent││ Agent    ││Debt Agent││  Agent    ││  Score   │
    └───────────┘└───────────┘└──────────┘└──────────┘└───────────┘└──────────┘
           │           │           │           │            │           │
           └───────────┴───────────┴─────┬─────┴────────────┴───────────┘
                                          ▼
                                 ┌─────────────────┐
                                 │  Report Agent    │
                                 └─────────────────┘
                                          │
                        ┌─────────────────┴─────────────────┐
                        ▼                                   ▼
                 ┌─────────────┐                    ┌───────────────┐
                 │  SQL DB      │                    │ ChromaDB (RAG) │
                 │ (users,      │                    │ optional —     │
                 │  profiles,   │                    │ investment tips│
                 │  budgets)    │                    │                │
                 └─────────────┘                    └───────────────┘
```

## Project Layout

```
smartbudget-ai/
├── main.py                     # FastAPI app: lifespan, CORS, routers, error handlers
├── app/
│   ├── core/                   # Cross-cutting concerns
│   │   ├── config.py           #   centralized settings (env / .env)
│   │   ├── security.py         #   password hashing + JWT
│   │   ├── logging_config.py   #   structured logging setup
│   │   └── exceptions.py       #   domain exceptions + handlers
│   ├── api/
│   │   ├── deps.py             # get_current_user, DB session dependency
│   │   └── v1/                 # versioned route modules
│   ├── services/
│   │   └── auth_service.py     # registration/login business logic
│   ├── agents/                 # the 7 specialized agents
│   ├── rag/                    # optional ChromaDB knowledge base
│   ├── db.py                   # SQLAlchemy models
│   ├── models.py                # Pydantic schemas
│   ├── orchestrator.py         # coordinates agents per request
│   └── llm.py                  # isolated Claude API access
├── frontend/                    # React (Vite) frontend
│   ├── src/
│   │   ├── pages/               #   Login, Register, ProfileSetup, LogExpense,
│   │   │                        #   Budget, HealthScore, Report
│   │   ├── components/          #   Layout (sidebar nav), ProtectedRoute
│   │   ├── context/AuthContext.jsx  # token/user state, login/register/logout
│   │   ├── api.js               #   axios instance + JWT interceptor
│   │   └── index.css            #   design tokens (ledger-book aesthetic)
│   ├── nginx.conf               # reverse proxy for /api/* in production
│   └── Dockerfile               # multi-stage: vite build -> nginx serve
├── frontend-streamlit/          # legacy Streamlit UI, kept for reference
│   └── app.py
├── tests/                      # pytest suite, 31 tests, 89% coverage
├── Dockerfile                  # backend image
├── docker-compose.yml          # backend + frontend together
├── .github/workflows/ci.yml    # lint + test + docker build on every push
├── pyproject.toml              # ruff + pytest config
└── .env.example
```

## Key Engineering Decisions

- **Auth is non-optional.** Every data endpoint requires a valid JWT. `user_id` is
  derived from the token server-side — it's never accepted from the request body —
  so one user can never read or write another user's financial data.
- **Wallet balance + category budgets, both tracked.** Saving your profile declares
  your income and resets `current_balance` to that amount for the month. Every
  logged expense reduces both the overall `current_balance` *and* that category's
  `BudgetItem.spent` — so you can see "how much do I have left overall" and
  "how much do I have left in groceries" at the same time.
- **Budget suggestions start smart and refine with data.** `GET /budget/suggested`
  blends an income-based starter estimate with the user's actual historical
  average spend per category (once they've logged some expenses), with a 10%
  buffer. Categories graduate from `"income-based estimate"` to
  `"your spending history"` one at a time as data accumulates —
  `personalization_level` reports `starter` / `partially_personalized` /
  `personalized` accordingly. `POST /budget/apply-suggested` writes the suggestion
  in as the active budget while preserving already-spent amounts.
- **Domain exceptions, not HTTPException scattered everywhere.** Agents and services
  raise `NotFoundError`, `ConflictError`, `AuthError`, etc. A single handler in
  `app/core/exceptions.py` converts them to consistent JSON responses and logs them.
- **ChromaDB is fully optional.** It requires a C++ compiler to build on Windows.
  If it's not installed, `app/rag/knowledge_base.py` transparently falls back to
  static tips — the app never crashes because of it.
- **LLM calls are isolated** in `app/llm.py`. Without `ANTHROPIC_API_KEY`, expense
  categorization falls back to keyword matching and report insights fall back to
  templated text — the whole app still works end-to-end for demos/interviews.
- **Settings are centralized** in `app/core/config.py` via `pydantic-settings`
  instead of `os.getenv()` calls scattered through the codebase.

## Setup (local, without Docker)

**1. Backend**
```bash
cd smartbudget-ai
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env            # edit JWT_SECRET_KEY at minimum
uvicorn main:app --reload
```
Backend runs at `http://localhost:8000` (interactive docs at `/docs`).

**2. Frontend** (second terminal)
```bash
cd frontend
npm install
npm run dev
```
Opens at `http://localhost:5173`. The Vite dev server proxies `/api/*` requests
to `http://localhost:8000` automatically (see `vite.config.js`) — no extra
configuration needed. Register an account, then walk through
Profile Setup → Log Expense → Budget → Health Score → Full Report.

## Setup (Docker)

```bash
cp .env.example .env    # set JWT_SECRET_KEY, optionally ANTHROPIC_API_KEY
docker compose up --build
```
Backend at `http://localhost:8000`, frontend at `http://localhost:5173`
(served by nginx, which proxies `/api/*` to the backend container internally).

## Running Tests

```bash
pip install -r requirements.txt   # includes pytest, pytest-cov, httpx
pytest --cov=app --cov-report=term-missing
```
31 tests covering auth, authorization boundaries, profile/expense/budget flows,
and pure agent logic (categorization, health scoring, debt strategies).

## Linting

```bash
pip install ruff
ruff check .
```

## API Overview

All endpoints below are prefixed with `/api/v1` and (except auth) require
`Authorization: Bearer <token>`.

| Method | Path | Description |
|---|---|---|
| POST | `/auth/register` | Create an account, returns a token |
| POST | `/auth/login` | Exchange email/password for a token |
| POST | `/profile` | Create/update the caller's financial profile (resets wallet balance to income) |
| POST | `/expense` | Log a natural-language expense (reduces wallet balance + category budget) |
| GET | `/expense/history` | List past transactions, most recent first; `?month=YYYY-MM` to filter |
| GET | `/budget` | Get the current month's budget + overall wallet balance |
| GET | `/budget/suggested` | A smart, self-refining budget suggestion |
| POST | `/budget/apply-suggested` | Apply the current suggestion as the active budget |
| GET | `/health-score` | Get the financial health score |
| GET | `/report` | Get the full monthly report |

`GET /healthz` (unprefixed) is a liveness probe for load balancers / Docker.

## What's Deliberately Simple (and how to extend it)

- **SQLite by default.** Swap to Postgres by setting `DATABASE_URL` — the code
  already branches on this.
- **No refresh tokens / token revocation list.** Access tokens are stateless JWTs
  with a 24h expiry. For production, add a refresh-token flow and a revocation
  store (e.g. Redis) for logout-everywhere support.
- **No rate limiting.** Add `slowapi` or a reverse-proxy-level limiter before
  exposing this publicly.
- **No database migrations.** Tables are created via `Base.metadata.create_all()`
  on startup. For schema evolution in production, add Alembic.

## Further Reading

- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — system diagram, request flow,
  layering, and the security model in detail.
- [`docs/adr/`](docs/adr/README.md) — Architecture Decision Records explaining
  *why* key choices were made (multi-agent design, JWT auth, SQLite→Postgres path).
