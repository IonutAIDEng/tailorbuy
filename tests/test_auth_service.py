from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest

from backend.models import RefreshToken, User
from backend.schemas.auth import UpdateProfileRequest
from backend.services import auth_service
from backend.services.auth_service import (
    _hash_token,
    change_password,
    create_access_token,
    get_me,
    hash_password,
    login,
    logout,
    refresh_tokens,
    register,
    update_profile,
    verify_access_token,
    verify_password,
)


# ── Passwords ──────────────────────────────────────────────────────────────

def test_hash_password_returns_different_from_plain():
    hashed = hash_password("secret")
    assert hashed != "secret"


def test_verify_password_correct():
    hashed = hash_password("secret")
    assert verify_password("secret", hashed) is True


def test_verify_password_wrong():
    hashed = hash_password("secret")
    assert verify_password("wrong", hashed) is False


# ── Access token ───────────────────────────────────────────────────────────

def test_create_access_token_returns_string():
    token = create_access_token(user_id=1)
    assert isinstance(token, str)
    assert len(token) > 0


def test_verify_access_token_valid():
    token = create_access_token(user_id=42)
    payload = verify_access_token(token)
    assert payload["sub"] == "42"
    assert payload["type"] == "access"


def test_verify_access_token_rejects_garbage():
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc:
        verify_access_token("not.a.token")
    assert exc.value.status_code == 401


def test_verify_access_token_rejects_expired():
    from fastapi import HTTPException
    import jwt
    from backend.config import JWT_SECRET_KEY
    from backend.constants import JWT_ALGORITHM
    payload = {
        "sub": "1",
        "type": "access",
        "exp": datetime.now(timezone.utc) - timedelta(seconds=1),
    }
    token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    with pytest.raises(HTTPException) as exc:
        verify_access_token(token)
    assert exc.value.status_code == 401


def test_verify_access_token_rejects_refresh_type():
    from fastapi import HTTPException
    import jwt
    from backend.config import JWT_SECRET_KEY
    from backend.constants import JWT_ALGORITHM
    payload = {
        "sub": "1",
        "type": "refresh",  # wrong type
        "exp": datetime.now(timezone.utc) + timedelta(minutes=15),
    }
    token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    with pytest.raises(HTTPException) as exc:
        verify_access_token(token)
    assert exc.value.status_code == 401


# ── Register ───────────────────────────────────────────────────────────────

def test_register_creates_user_and_returns_tokens(db):
    result = register(db, "user@example.com", "password123")
    assert result.access_token
    assert result.refresh_token
    assert result.token_type == "bearer"
    user = db.query(User).filter(User.email == "user@example.com").first()
    assert user is not None
    assert user.nickname is None


def test_register_stores_nickname(db):
    register(db, "user@example.com", "password123", nickname="Andrei")
    user = db.query(User).filter(User.email == "user@example.com").first()
    assert user.nickname == "Andrei"


def test_register_duplicate_email_raises_409(db):
    from fastapi import HTTPException
    register(db, "user@example.com", "password123")
    with pytest.raises(HTTPException) as exc:
        register(db, "user@example.com", "otherpassword")
    assert exc.value.status_code == 409


def test_register_stores_refresh_token_hash(db):
    result = register(db, "user@example.com", "password123")
    token_hash = _hash_token(result.refresh_token)
    record = db.query(RefreshToken).filter(RefreshToken.token_hash == token_hash).first()
    assert record is not None
    assert record.revoked_at is None


# ── Login ──────────────────────────────────────────────────────────────────

def test_login_success(db, user):
    result = login(db, "test@example.com", "testpassword")
    assert result.access_token
    assert result.refresh_token


def test_login_wrong_password_raises_401(db, user):
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc:
        login(db, "test@example.com", "wrongpassword")
    assert exc.value.status_code == 401


def test_login_unknown_email_raises_401(db):
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc:
        login(db, "nobody@example.com", "anypassword")
    assert exc.value.status_code == 401


def test_login_inactive_user_raises_403(db, user):
    from fastapi import HTTPException
    user.is_active = False
    db.commit()
    with pytest.raises(HTTPException) as exc:
        login(db, "test@example.com", "testpassword")
    assert exc.value.status_code == 403


# ── Refresh tokens ─────────────────────────────────────────────────────────

def test_refresh_tokens_returns_new_pair(db, user):
    initial = login(db, "test@example.com", "testpassword")
    result = refresh_tokens(db, initial.refresh_token)
    # Refresh token must always be a new random value
    assert result.refresh_token != initial.refresh_token
    # Access tokens are deterministic JWT — may match if issued within the same second, which is fine
    assert result.access_token  # non-empty is sufficient here


def test_refresh_marks_old_token_as_revoked(db, user):
    initial = login(db, "test@example.com", "testpassword")
    old_hash = _hash_token(initial.refresh_token)
    refresh_tokens(db, initial.refresh_token)
    old_record = db.query(RefreshToken).filter(RefreshToken.token_hash == old_hash).first()
    assert old_record.revoked_at is not None


def test_refresh_reuse_revokes_all_sessions(db, user):
    from fastapi import HTTPException
    initial = login(db, "test@example.com", "testpassword")
    refresh_tokens(db, initial.refresh_token)  # rotate once — old token is now revoked
    with pytest.raises(HTTPException) as exc:
        refresh_tokens(db, initial.refresh_token)  # reuse the already-rotated token
    assert exc.value.status_code == 401
    remaining = db.query(RefreshToken).filter(RefreshToken.user_id == user.id).count()
    assert remaining == 0  # all sessions wiped


def test_refresh_invalid_token_raises_401(db):
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc:
        refresh_tokens(db, "totally-fake-token")
    assert exc.value.status_code == 401


def test_refresh_expired_token_raises_401(db, user):
    from fastapi import HTTPException
    initial = login(db, "test@example.com", "testpassword")
    token_hash = _hash_token(initial.refresh_token)
    record = db.query(RefreshToken).filter(RefreshToken.token_hash == token_hash).first()
    record.expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
    db.commit()
    with pytest.raises(HTTPException) as exc:
        refresh_tokens(db, initial.refresh_token)
    assert exc.value.status_code == 401


# ── Logout ─────────────────────────────────────────────────────────────────

def test_logout_removes_refresh_token(db, user):
    result = login(db, "test@example.com", "testpassword")
    token_hash = _hash_token(result.refresh_token)
    logout(db, result.refresh_token)
    record = db.query(RefreshToken).filter(RefreshToken.token_hash == token_hash).first()
    assert record is None


def test_logout_unknown_token_is_no_op(db):
    logout(db, "nonexistent-token")  # must not raise


# ── Profile ────────────────────────────────────────────────────────────────

def test_get_me_returns_user_data(user):
    result = get_me(user)
    assert result.id == user.id
    assert result.email == "test@example.com"
    assert result.nickname == "Tester"


def test_update_profile_changes_nickname(db, user):
    result = update_profile(db, user, UpdateProfileRequest(nickname="NewName"))
    assert result.nickname == "NewName"
    db.refresh(user)
    assert user.nickname == "NewName"


def test_update_profile_changes_email(db, user):
    result = update_profile(db, user, UpdateProfileRequest(email="new@example.com"))
    assert result.email == "new@example.com"


def test_update_profile_email_conflict_raises_409(db, user):
    from fastapi import HTTPException
    other = User(email="other@example.com", hashed_password=hash_password("pw12345678"))
    db.add(other)
    db.commit()
    with pytest.raises(HTTPException) as exc:
        update_profile(db, user, UpdateProfileRequest(email="other@example.com"))
    assert exc.value.status_code == 409


def test_update_profile_no_fields_is_no_op(db, user):
    result = update_profile(db, user, UpdateProfileRequest())
    assert result.email == user.email
    assert result.nickname == user.nickname


def test_change_password_success(db, user):
    change_password(db, user, "testpassword", "newpassword123")
    assert verify_password("newpassword123", user.hashed_password)


def test_change_password_revokes_all_refresh_tokens(db, user):
    login(db, "test@example.com", "testpassword")
    login(db, "test@example.com", "testpassword")
    change_password(db, user, "testpassword", "newpassword123")
    remaining = db.query(RefreshToken).filter(RefreshToken.user_id == user.id).count()
    assert remaining == 0


def test_change_password_wrong_current_raises_400(db, user):
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc:
        change_password(db, user, "wrongpassword", "newpassword123")
    assert exc.value.status_code == 400


def test_change_password_same_as_current_raises_400(db, user):
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc:
        change_password(db, user, "testpassword", "testpassword")
    assert exc.value.status_code == 400
