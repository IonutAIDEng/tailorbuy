from unittest.mock import patch

import pytest

from backend.models import User
from backend.services.auth_service import hash_password, login


# ── Register ───────────────────────────────────────────────────────────────

def test_register_returns_201_with_tokens(client):
    response = client.post("/auth/register", json={
        "email": "new@example.com",
        "password": "password123",
    })
    assert response.status_code == 201
    body = response.json()
    assert "access_token" in body
    assert "refresh_token" in body
    assert body["token_type"] == "bearer"


def test_register_with_nickname(client):
    response = client.post("/auth/register", json={
        "email": "new@example.com",
        "password": "password123",
        "nickname": "Andrei",
    })
    assert response.status_code == 201


def test_register_duplicate_email_returns_409(client, user):
    response = client.post("/auth/register", json={
        "email": "test@example.com",
        "password": "password123",
    })
    assert response.status_code == 409


def test_register_invalid_email_returns_422(client):
    response = client.post("/auth/register", json={
        "email": "notanemail",
        "password": "password123",
    })
    assert response.status_code == 422


def test_register_short_password_returns_422(client):
    response = client.post("/auth/register", json={
        "email": "user@example.com",
        "password": "short",
    })
    assert response.status_code == 422


def test_register_nickname_too_long_returns_422(client):
    response = client.post("/auth/register", json={
        "email": "user@example.com",
        "password": "password123",
        "nickname": "x" * 31,
    })
    assert response.status_code == 422


# ── Login ──────────────────────────────────────────────────────────────────

def test_login_returns_tokens(client, user):
    response = client.post("/auth/login", json={
        "email": "test@example.com",
        "password": "testpassword",
    })
    assert response.status_code == 200
    body = response.json()
    assert "access_token" in body
    assert "refresh_token" in body


def test_login_wrong_password_returns_401(client, user):
    response = client.post("/auth/login", json={
        "email": "test@example.com",
        "password": "wrongpassword",
    })
    assert response.status_code == 401


def test_login_unknown_email_returns_401(client):
    response = client.post("/auth/login", json={
        "email": "nobody@example.com",
        "password": "anypassword",
    })
    assert response.status_code == 401


def test_login_email_is_case_insensitive(client, user):
    response = client.post("/auth/login", json={
        "email": "TEST@EXAMPLE.COM",
        "password": "testpassword",
    })
    assert response.status_code == 200


# ── Refresh ────────────────────────────────────────────────────────────────

def test_refresh_returns_new_tokens(client, user):
    login_res = client.post("/auth/login", json={"email": "test@example.com", "password": "testpassword"})
    refresh_token = login_res.json()["refresh_token"]

    response = client.post("/auth/refresh", json={"refresh_token": refresh_token})
    assert response.status_code == 200
    body = response.json()
    assert body["refresh_token"] != refresh_token


def test_refresh_invalid_token_returns_401(client):
    response = client.post("/auth/refresh", json={"refresh_token": "fakefakefake"})
    assert response.status_code == 401


def test_refresh_reuse_returns_401(client, user):
    login_res = client.post("/auth/login", json={"email": "test@example.com", "password": "testpassword"})
    refresh_token = login_res.json()["refresh_token"]
    client.post("/auth/refresh", json={"refresh_token": refresh_token})
    response = client.post("/auth/refresh", json={"refresh_token": refresh_token})
    assert response.status_code == 401


# ── Logout ─────────────────────────────────────────────────────────────────

def test_logout_returns_204(client, user):
    login_res = client.post("/auth/login", json={"email": "test@example.com", "password": "testpassword"})
    refresh_token = login_res.json()["refresh_token"]

    response = client.post("/auth/logout", json={"refresh_token": refresh_token})
    assert response.status_code == 204
    assert response.content == b""


def test_logout_then_refresh_returns_401(client, user):
    login_res = client.post("/auth/login", json={"email": "test@example.com", "password": "testpassword"})
    refresh_token = login_res.json()["refresh_token"]
    client.post("/auth/logout", json={"refresh_token": refresh_token})

    response = client.post("/auth/refresh", json={"refresh_token": refresh_token})
    assert response.status_code == 401


# ── Protected endpoints ────────────────────────────────────────────────────

def test_get_me_returns_user_data(auth_client, user):
    response = auth_client.get("/auth/me")
    assert response.status_code == 200
    body = response.json()
    assert body["email"] == "test@example.com"
    assert body["nickname"] == "Tester"
    assert "id" in body


def test_get_me_without_auth_returns_401_or_403(client):
    response = client.get("/auth/me")
    assert response.status_code in (401, 403)


def test_update_profile_changes_nickname(auth_client, user):
    response = auth_client.put("/auth/me", json={"nickname": "NewNick"})
    assert response.status_code == 200
    assert response.json()["nickname"] == "NewNick"


def test_update_profile_changes_email(auth_client, user):
    response = auth_client.put("/auth/me", json={"email": "updated@example.com"})
    assert response.status_code == 200
    assert response.json()["email"] == "updated@example.com"


def test_change_password_returns_204(auth_client, user):
    response = auth_client.post("/auth/change-password", json={
        "current_password": "testpassword",
        "new_password": "newpassword123",
    })
    assert response.status_code == 204


def test_change_password_wrong_current_returns_400(auth_client, user):
    response = auth_client.post("/auth/change-password", json={
        "current_password": "wrongpassword",
        "new_password": "newpassword123",
    })
    assert response.status_code == 400


def test_change_password_same_password_returns_400(auth_client, user):
    response = auth_client.post("/auth/change-password", json={
        "current_password": "testpassword",
        "new_password": "testpassword",
    })
    assert response.status_code == 400
