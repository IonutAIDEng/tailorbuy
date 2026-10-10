from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, Date, DateTime, Float, ForeignKey, Integer, String

from backend.database import Base


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    # False = soft-banned (keeps data, blocks login) — never delete users
    is_active = Column(Boolean, nullable=False, default=True, server_default='true')
    nickname = Column(String(30), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    searches_today = Column(Integer, nullable=False, default=0, server_default='0')
    last_search_date = Column(Date, nullable=True)


class UserPreference(Base):
    __tablename__ = 'users_preferences'
    id = Column(Integer, primary_key=True)
    cash_only = Column(Boolean)
    open_package = Column(Boolean)
    min_rating = Column(Float)
    max_price = Column(Integer, nullable=True, default=None)
    min_review_count = Column(Integer, nullable=True, default=None)
    new_only = Column(Boolean, nullable=False, default=False, server_default='false')
    search_emag = Column(Boolean, nullable=False, default=True, server_default='true')
    search_altex = Column(Boolean, nullable=False, default=True, server_default='true')
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)


class RefreshToken(Base):
    __tablename__ = 'refresh_tokens'
    id = Column(Integer, primary_key=True)
    # CASCADE: deleting a user automatically deletes all their refresh tokens
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    # We store SHA-256(raw_token), never the token itself — same principle as hashed passwords
    token_hash = Column(String(64), nullable=False, unique=True, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    # Non-null = this token was rotated; if it's submitted again → reuse detected → revoke all sessions
    revoked_at = Column(DateTime(timezone=True), nullable=True)
