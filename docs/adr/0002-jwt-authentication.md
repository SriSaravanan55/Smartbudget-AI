# ADR 0002: JWT bearer authentication, user identity derived server-side

## Status
Accepted

## Context
The original prototype took `user_id` as a plain request field/path parameter
on every endpoint. That's fine for a local demo but is a real vulnerability
once the app is reachable over a network: any caller could read or modify
another user's financial data simply by changing the `user_id` in the
request — an IDOR (Insecure Direct Object Reference) vulnerability.

## Decision
- Add a `User` table (email, hashed password) separate from the financial
  `UserProfile` table.
- `POST /api/v1/auth/register` and `POST /api/v1/auth/login` issue a JWT
  whose `sub` claim is the user's `user_id`.
- All other endpoints require `Authorization: Bearer <token>`, decode it via
  `app/api/deps.py::get_current_user`, and use *only* the resulting
  server-verified `user_id` — client input can no longer specify whose data
  to read or write.
- Passwords are hashed with bcrypt via `passlib`; plaintext passwords are
  never persisted or logged.

## Consequences
- Every profile/expense/budget/report route now requires a `current_user`
  dependency, which is enforced by a test
  (`test_users_cannot_access_each_others_data`) that registers two users and
  asserts one cannot read the other's budget.
- The frontend must hold a session token and attach it to every request; a
  login/register gate was added to the Streamlit UI.
- Tokens are stateless (no server-side session store), so logout is
  client-side only (discarding the token). If token revocation before
  natural expiry becomes a requirement, a denylist or short-lived
  access + refresh token pair would need to be added.
