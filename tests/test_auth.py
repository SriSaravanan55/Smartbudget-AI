"""Tests for registration and login."""


def test_register_creates_user_and_returns_token(client):
    resp = client.post("/api/v1/auth/register", json={
        "user_id": "alice", "email": "alice@example.com", "password": "securepass1",
    })
    assert resp.status_code == 201
    body = resp.json()
    assert body["user_id"] == "alice"
    assert body["access_token"]
    assert body["token_type"] == "bearer"


def test_register_duplicate_user_id_fails(client):
    payload = {"user_id": "alice", "email": "alice@example.com", "password": "securepass1"}
    client.post("/api/v1/auth/register", json=payload)
    resp = client.post("/api/v1/auth/register", json={**payload, "email": "different@example.com"})
    assert resp.status_code == 409


def test_register_duplicate_email_fails(client):
    client.post("/api/v1/auth/register", json={
        "user_id": "alice", "email": "shared@example.com", "password": "securepass1",
    })
    resp = client.post("/api/v1/auth/register", json={
        "user_id": "bob", "email": "shared@example.com", "password": "securepass1",
    })
    assert resp.status_code == 409


def test_register_rejects_short_password(client):
    resp = client.post("/api/v1/auth/register", json={
        "user_id": "alice", "email": "alice@example.com", "password": "short",
    })
    assert resp.status_code == 422


def test_login_with_correct_credentials_succeeds(client):
    client.post("/api/v1/auth/register", json={
        "user_id": "alice", "email": "alice@example.com", "password": "securepass1",
    })
    resp = client.post("/api/v1/auth/login", json={
        "email": "alice@example.com", "password": "securepass1",
    })
    assert resp.status_code == 200
    assert resp.json()["access_token"]


def test_login_with_wrong_password_fails(client):
    client.post("/api/v1/auth/register", json={
        "user_id": "alice", "email": "alice@example.com", "password": "securepass1",
    })
    resp = client.post("/api/v1/auth/login", json={
        "email": "alice@example.com", "password": "wrongpassword",
    })
    assert resp.status_code == 401


def test_login_with_unknown_email_fails(client):
    resp = client.post("/api/v1/auth/login", json={
        "email": "nobody@example.com", "password": "whatever123",
    })
    assert resp.status_code == 401
