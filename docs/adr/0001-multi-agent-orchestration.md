# ADR 0001: Multi-agent orchestration instead of one monolithic service

## Status
Accepted

## Context
SmartBudget AI needs to: build a user profile, categorize free-text expenses,
generate a budget, plan debt payoff, give investment guidance, score
financial health, and compile a report. These are distinct domains with
different inputs, different failure modes, and different rates of change
(e.g. the categorization logic is likely to gain an LLM-based rewrite long
before the health-score formula changes).

## Decision
Each domain is implemented as an independent agent class under `app/agents/`
with a narrow, single-purpose interface (e.g. `BudgetAgent.generate_budget`).
A thin `Orchestrator` composes them per request. Agents do not call each
other directly or share mutable state; they communicate through plain dicts
and the database.

## Consequences
- **Testability**: each agent can be unit-tested in isolation with plain
  Python objects (see `tests/test_agents.py`) — no HTTP layer, no auth, no
  mocking chains.
- **Independent evolution**: `CategorizationAgent` can swap its LLM prompt or
  fall back to rules without touching `BudgetAgent` or the API layer.
- **Explicit coordination point**: business rules that span multiple agents
  (e.g. "regenerate the budget whenever the profile changes") live in one
  place — the orchestrator — instead of being scattered across route
  handlers.
- **Trade-off**: for a system this size, a single service class would also
  have worked and would have less indirection. We accepted the extra
  boilerplate because the project is explicitly meant to demonstrate
  agent-based decomposition, and because financial-domain logic (scoring
  formulas, budget weighting) tends to accrete edge cases that benefit from
  being isolated.
