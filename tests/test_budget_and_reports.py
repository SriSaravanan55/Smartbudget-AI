"""Tests for budget generation, health score, and full report endpoints."""


def _create_profile(client, headers, **overrides):
    payload = {
        "monthly_income": 60000,
        "risk_tolerance": "moderate",
        "savings_goal": 8000,
        "emergency_fund_target": 180000,
        "emergency_fund_current": 30000,
        "debts": [{"name": "Education Loan", "balance": 200000, "interest_rate": 9.5, "min_payment": 4000}],
    }
    payload.update(overrides)
    return client.post("/api/v1/profile", json=payload, headers=headers)


def test_budget_requires_existing_profile(client, auth_headers):
    resp = client.get("/api/v1/budget", headers=auth_headers)
    assert resp.status_code == 404


def test_budget_is_generated_after_profile_creation(client, auth_headers):
    _create_profile(client, auth_headers)
    resp = client.get("/api/v1/budget", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["total_income"] == 60000
    assert len(body["categories"]) > 0
    # Allocations should never exceed income
    total_allocated = sum(c["allocated"] for c in body["categories"])
    assert total_allocated <= body["total_income"]


def test_budget_reserves_minimum_debt_payments(client, auth_headers):
    _create_profile(client, auth_headers)
    resp = client.get("/api/v1/budget", headers=auth_headers)
    categories = {c["category"]: c for c in resp.json()["categories"]}
    assert "debt_payment" in categories
    assert categories["debt_payment"]["allocated"] == 4000.0


def test_health_score_returns_0_to_100(client, auth_headers):
    _create_profile(client, auth_headers)
    resp = client.get("/api/v1/health-score", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert 0 <= body["score"] <= 100
    assert set(body["breakdown"].keys()) == {
        "savings_rate_score", "debt_to_income_score",
        "emergency_fund_score", "budget_adherence_score",
    }


def test_full_report_includes_all_sections(client, auth_headers):
    _create_profile(client, auth_headers)
    client.post("/api/v1/expense", json={"text": "spent 500 on groceries"}, headers=auth_headers)

    resp = client.get("/api/v1/report", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert "budget" in body
    assert "health_score" in body
    assert "savings_progress" in body
    assert "debt_plan" in body
    assert len(body["insights"]) > 0
    assert len(body["action_items"]) > 0


def test_users_cannot_access_each_others_data(client):
    # User A
    r1 = client.post("/api/v1/auth/register", json={
        "user_id": "usera", "email": "a@example.com", "password": "passwordA1",
    })
    headers_a = {"Authorization": f"Bearer {r1.json()['access_token']}"}
    _create_profile(client, headers_a, monthly_income=100000)

    # User B
    r2 = client.post("/api/v1/auth/register", json={
        "user_id": "userb", "email": "b@example.com", "password": "passwordB1",
    })
    headers_b = {"Authorization": f"Bearer {r2.json()['access_token']}"}

    # B has no profile yet -- must get 404, never see A's budget
    resp = client.get("/api/v1/budget", headers=headers_b)
    assert resp.status_code == 404

    # A's own budget reflects A's own income, unaffected by B
    resp = client.get("/api/v1/budget", headers=headers_a)
    assert resp.json()["total_income"] == 100000
