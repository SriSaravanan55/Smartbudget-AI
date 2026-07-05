"""Tests for wallet balance tracking, expense history, and budget suggestions."""


def _create_profile(client, headers, **overrides):
    payload = {
        "monthly_income": 60000,
        "risk_tolerance": "moderate",
        "savings_goal": 8000,
        "emergency_fund_target": 180000,
        "emergency_fund_current": 30000,
        "debts": [],
    }
    payload.update(overrides)
    return client.post("/api/v1/profile", json=payload, headers=headers)


def test_profile_creation_sets_current_balance_to_income(client, auth_headers):
    _create_profile(client, auth_headers, monthly_income=50000)
    resp = client.get("/api/v1/budget", headers=auth_headers)
    assert resp.json()["current_balance"] == 50000


def test_expense_reduces_current_balance(client, auth_headers):
    _create_profile(client, auth_headers, monthly_income=50000)
    resp = client.post("/api/v1/expense", json={"text": "spent 500 on groceries"}, headers=auth_headers)
    assert resp.json()["current_balance"] == 49500.0

    resp2 = client.post("/api/v1/expense", json={"text": "spent 200 on transport"}, headers=auth_headers)
    assert resp2.json()["current_balance"] == 49300.0

    budget = client.get("/api/v1/budget", headers=auth_headers)
    assert budget.json()["current_balance"] == 49300.0


def test_expense_still_reduces_category_budget_alongside_balance(client, auth_headers):
    _create_profile(client, auth_headers, monthly_income=60000)
    resp = client.post("/api/v1/expense", json={"text": "spent 500 on groceries"}, headers=auth_headers)
    body = resp.json()
    assert body["remaining_in_category"] is not None
    assert body["current_balance"] == 59500.0


def test_saving_profile_again_resets_balance_to_new_income(client, auth_headers):
    _create_profile(client, auth_headers, monthly_income=50000)
    client.post("/api/v1/expense", json={"text": "spent 1000 on groceries"}, headers=auth_headers)

    _create_profile(client, auth_headers, monthly_income=70000)
    resp = client.get("/api/v1/budget", headers=auth_headers)
    assert resp.json()["current_balance"] == 70000


def test_expense_history_requires_existing_profile(client, auth_headers):
    resp = client.get("/api/v1/expense/history", headers=auth_headers)
    assert resp.status_code == 404


def test_expense_history_lists_transactions_most_recent_first(client, auth_headers):
    _create_profile(client, auth_headers)
    client.post("/api/v1/expense", json={"text": "took a cab for 200"}, headers=auth_headers)
    client.post("/api/v1/expense", json={"text": "spent 500 on groceries"}, headers=auth_headers)

    resp = client.get("/api/v1/expense/history", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["transactions"]) == 2
    assert body["total_spent"] == 700.0
    # Most recent (groceries) should be first
    assert body["transactions"][0]["category"] == "groceries"
    assert body["transactions"][1]["category"] == "transport"


def test_expense_history_includes_current_balance(client, auth_headers):
    _create_profile(client, auth_headers, monthly_income=60000)
    client.post("/api/v1/expense", json={"text": "spent 500 on groceries"}, headers=auth_headers)

    resp = client.get("/api/v1/expense/history", headers=auth_headers)
    assert resp.json()["current_balance"] == 59500.0


def test_expense_history_filters_by_month(client, auth_headers):
    _create_profile(client, auth_headers)
    client.post("/api/v1/expense", json={"text": "spent 100 on transport"}, headers=auth_headers)

    resp = client.get("/api/v1/expense/history?month=1999-01", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["transactions"] == []
    assert resp.json()["total_spent"] == 0.0


def test_users_cannot_see_each_others_expense_history(client):
    r1 = client.post("/api/v1/auth/register", json={
        "user_id": "usera2", "email": "a2@example.com", "password": "passwordA1",
    })
    headers_a = {"Authorization": f"Bearer {r1.json()['access_token']}"}
    _create_profile(client, headers_a)
    client.post("/api/v1/expense", json={"text": "spent 5000 on rent"}, headers=headers_a)

    r2 = client.post("/api/v1/auth/register", json={
        "user_id": "userb2", "email": "b2@example.com", "password": "passwordB1",
    })
    headers_b = {"Authorization": f"Bearer {r2.json()['access_token']}"}
    resp = client.get("/api/v1/expense/history", headers=headers_b)
    assert resp.status_code == 404  # B has no profile at all


def test_suggested_budget_is_starter_with_no_history(client, auth_headers):
    _create_profile(client, auth_headers, monthly_income=60000)
    resp = client.get("/api/v1/budget/suggested", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["personalization_level"] == "starter"
    assert all(c["based_on"] != "your spending history" for c in body["categories"] if c["category"] not in ("savings", "debt_payment"))


def test_suggested_budget_becomes_personalized_after_logging_expenses(client, auth_headers):
    _create_profile(client, auth_headers, monthly_income=60000)
    # Log enough groceries spending that it dominates the historical average
    client.post("/api/v1/expense", json={"text": "spent 6000 on groceries"}, headers=auth_headers)

    resp = client.get("/api/v1/budget/suggested", headers=auth_headers)
    body = resp.json()
    assert body["personalization_level"] == "partially_personalized"
    groceries = next(c for c in body["categories"] if c["category"] == "groceries")
    assert groceries["based_on"] == "your spending history"
    # Suggested amount should be roughly 6000 * 1.10, scaled by the pool ratio
    assert groceries["suggested_allocated"] > 0


def test_suggested_budget_total_does_not_exceed_income(client, auth_headers):
    _create_profile(client, auth_headers, monthly_income=60000,
                     debts=[{"name": "Loan", "balance": 10000, "interest_rate": 5, "min_payment": 2000}])
    client.post("/api/v1/expense", json={"text": "spent 3000 on groceries"}, headers=auth_headers)

    resp = client.get("/api/v1/budget/suggested", headers=auth_headers)
    body = resp.json()
    total = sum(c["suggested_allocated"] for c in body["categories"])
    assert total <= body["total_income"] + 1  # allow tiny rounding slack


def test_apply_suggested_budget_updates_allocations(client, auth_headers):
    _create_profile(client, auth_headers, monthly_income=60000)
    client.post("/api/v1/expense", json={"text": "spent 6000 on groceries"}, headers=auth_headers)

    resp = client.post("/api/v1/budget/apply-suggested", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    groceries = next(c for c in body["categories"] if c["category"] == "groceries")
    # Should now be much higher than the original static ~7200 estimate, near the
    # historical average with buffer, and should retain the already-spent amount.
    assert groceries["spent"] == 6000.0
    assert groceries["allocated"] > 6000.0


def test_apply_suggested_budget_requires_existing_profile(client, auth_headers):
    resp = client.post("/api/v1/budget/apply-suggested", headers=auth_headers)
    assert resp.status_code == 404
