import hashlib
import secrets
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from backend.config import JWT_SECRET_KEY
from backend.constants import ACCESS_TOKEN_EXPIRE_MINUTES, JWT_ALGORITHM, REFRESH_TOKEN_EXPIRE_DAYS
from backend.models import RefreshToken, User
from backend.schemas.auth import MeResponse, TokenResponse, UpdateProfileRequest


_BCRYPT_ROUNDS = 12  # each +1 doubles compute time; 12 ≈ 250ms — too slow for bots, invisible to humans

# Pre-computed once at startup. Used in login() to run bcrypt even when email is not found,
# preventing timing-based email enumeration (response time would otherwise reveal valid emails).
_DUMMY_HASH: str = bcrypt.hashpw(b"timing-equalization-dummy", bcrypt.gensalt(rounds=_BCRYPT_ROUNDS)).decode()

_CREDENTIALS_ERROR = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Email sau parolă incorectă",
    headers={"WWW-Authenticate": "Bearer"},
)


# ── Passwords ──────────────────────────────────────────────────────────────

def hash_password(plain: str) -> str:
    """Return a bcrypt hash of the plain-text password. Store this, never the original."""
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt(rounds=_BCRYPT_ROUNDS)).decode()


def verify_password(plain: str, hashed: str) -> bool:
    """Return True if plain matches the stored bcrypt hash. Uses constant-time comparison."""
    return bcrypt.checkpw(plain.encode(), hashed.encode())


# ── Access token (JWT) ─────────────────────────────────────────────────────

def create_access_token(user_id: int) -> str:
    """Create a signed JWT access token valid for ACCESS_TOKEN_EXPIRE_MINUTES. Never stored server-side."""
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),          # subject — who this token belongs to
        "iat": now,                   # issued at
        "exp": now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
        "type": "access",             # guards against using a refresh token as access
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def verify_access_token(token: str) -> dict:
    """Decode and validate an access token. Raises 401 on any failure."""
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Token expirat", headers={"WWW-Authenticate": "Bearer"})
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Token invalid", headers={"WWW-Authenticate": "Bearer"})

    if payload.get("type") != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Token invalid", headers={"WWW-Authenticate": "Bearer"})
    return payload


def _hash_token(raw: str) -> str:
    """SHA-256 hex digest of the raw refresh token. Only this hash is stored in the DB."""
    return hashlib.sha256(raw.encode()).hexdigest()


def _create_refresh_token_record(db: Session, user_id: int) -> str:
    """Insert a new refresh token row in DB and return the raw (unhashed) token for the client."""
    raw = secrets.token_urlsafe(32)
    record = RefreshToken(
        user_id=user_id,
        token_hash=_hash_token(raw),
        expires_at=datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
    )
    db.add(record)
    db.commit()
    return raw


# ── Register ───────────────────────────────────────────────────────────────

def register(db: Session, email: str, password: str, nickname: str | None = None) -> TokenResponse:
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail="Există deja un cont cu acest email")

    user = User(email=email, hashed_password=hash_password(password), nickname=nickname)
    db.add(user)
    db.commit()
    db.refresh(user)

    access = create_access_token(user.id)
    refresh = _create_refresh_token_record(db, user.id)
    return TokenResponse(access_token=access, refresh_token=refresh)


# ── Login ──────────────────────────────────────────────────────────────────

def login(db: Session, email: str, password: str) -> TokenResponse:
    user = db.query(User).filter(User.email == email).first()
    # Always run bcrypt regardless of whether the user exists.
    # Without this, a missing user returns in ~1ms (no bcrypt) vs ~250ms for wrong password,
    # leaking which emails are registered via response timing.
    candidate_hash = user.hashed_password if user else _DUMMY_HASH
    password_valid = verify_password(password, candidate_hash)
    if not user or not password_valid:
        raise _CREDENTIALS_ERROR

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Utilizator este inactiv")

    access = create_access_token(user.id)
    refresh = _create_refresh_token_record(db, user.id)
    return TokenResponse(access_token=access, refresh_token=refresh)


# ── Refresh ────────────────────────────────────────────────────────────────

def refresh_tokens(db: Session, raw_token: str) -> TokenResponse:
    token_hash = _hash_token(raw_token)
    record = db.query(RefreshToken).filter(RefreshToken.token_hash == token_hash).first()

    if record is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Token invalid sau expirat")

    if record.revoked_at is not None:
        # Reuse of an already-rotated token: possible theft — revoke all user sessions
        db.query(RefreshToken).filter(RefreshToken.user_id == record.user_id).delete()
        db.commit()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Token reutilizat — toate sesiunile au fost invalidate")

    # SQLite returns offset-naive datetimes; PostgreSQL returns offset-aware — normalise for both
    expires_at = record.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at < datetime.now(timezone.utc):
        db.delete(record)
        db.commit()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Token expirat")

    now = datetime.now(timezone.utc)

    # Mark old token as rotated (kept for 7-day reuse detection window)
    record.revoked_at = now
    db.commit()

    # Lazy cleanup: purge revoked tokens whose reuse-detection window has expired.
    # Runs on every successful refresh so the table never grows unboundedly.
    # Use naive UTC for the comparison: SQLite stores datetimes without tz info;
    # PostgreSQL handles both, so naive UTC is the lowest common denominator.
    cleanup_cutoff = now.replace(tzinfo=None)
    db.query(RefreshToken).filter(
        RefreshToken.user_id == record.user_id,
        RefreshToken.revoked_at.isnot(None),
        RefreshToken.expires_at < cleanup_cutoff,
    ).delete()
    db.commit()

    access = create_access_token(record.user_id)
    new_refresh = _create_refresh_token_record(db, record.user_id)
    return TokenResponse(access_token=access, refresh_token=new_refresh)


# ── Logout ─────────────────────────────────────────────────────────────────

def logout(db: Session, raw_token: str) -> None:
    token_hash = _hash_token(raw_token)
    db.query(RefreshToken).filter(RefreshToken.token_hash == token_hash).delete()
    db.commit()


# ── Profile ────────────────────────────────────────────────────────────────

def get_me(user: User) -> MeResponse:
    return MeResponse(id=user.id, email=user.email, nickname=user.nickname)


def update_profile(db: Session, user: User, request: UpdateProfileRequest) -> MeResponse:
    if request.email is not None and request.email != user.email:
        conflict = db.query(User).filter(User.email == request.email, User.id != user.id).first()
        if conflict:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                                detail="Email deja folosit de alt cont")
        user.email = request.email

    if request.nickname is not None:
        user.nickname = request.nickname

    db.commit()
    db.refresh(user)
    return MeResponse(id=user.id, email=user.email, nickname=user.nickname)


def change_password(db: Session, user: User, current_password: str, new_password: str) -> None:
    if not verify_password(current_password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Parola curentă este incorectă")
    if new_password == current_password:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Noua parolă trebuie să fie diferită de cea actuală")

    user.hashed_password = hash_password(new_password)
    # Revoke all refresh tokens — forces re-login on all devices after password change
    db.query(RefreshToken).filter(RefreshToken.user_id == user.id).delete()
    db.commit()
