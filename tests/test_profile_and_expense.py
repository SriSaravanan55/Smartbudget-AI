"""Tests for profile creation and expense logging, including auth enforcement."""


def test_profile_requires_authentication(client):
    resp = client.post("/api/v1/profile", json={"monthly_income": 50000})
    assert resp.status_code == 401


def test_create_profile_succeeds_when_authenticated(client, auth_headers):
    resp = client.post("/api/v1/profile", json={
        "monthly_income": 60000,
        "risk_tolerance": "moderate",
        "savings_goal": 8000,
        "emergency_fund_target": 180000,
        "emergency_fund_current": 30000,
        "debts": [],
    }, headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["user_id"] == "testuser"


def test_profile_rejects_negative_income(client, auth_headers):
    resp = client.post("/api/v1/profile", json={"monthly_income": -100}, headers=auth_headers)
    assert resp.status_code == 422


def test_profile_rejects_invalid_risk_tolerance(client, auth_headers):
    resp = client.post("/api/v1/profile", json={
        "monthly_income": 50000, "risk_tolerance": "extreme",
    }, headers=auth_headers)
    assert resp.status_code == 422


def test_expense_requires_existing_profile(client, auth_headers):
    resp = client.post("/api/v1/expense", json={"text": "spent 200 on groceries"}, headers=auth_headers)
    assert resp.status_code == 404


def test_log_expense_categorizes_and_updates_budget(client, auth_headers):
    client.post("/api/v1/profile", json={"monthly_income": 60000}, headers=auth_headers)
    resp = client.post("/api/v1/expense", json={"text": "spent 500 on groceries"}, headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["category"] == "groceries"
    assert body["amount"] == 500.0
    assert body["remaining_in_category"] is not None


def test_expense_requires_authentication(client):
    resp = client.post("/api/v1/expense", json={"text": "spent 100 on transport"})
    assert resp.status_code == 401


def test_invalid_token_is_rejected(client):
    resp = client.get("/api/v1/budget", headers={"Authorization": "Bearer not-a-real-token"})
    assert resp.status_code == 401
