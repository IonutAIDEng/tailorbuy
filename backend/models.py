from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, Float, DateTime

from backend.database import Base


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    device_id = Column(String, unique=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class UserPreference(Base):
    __tablename__ = 'users_preferences'
    id = Column(Integer, primary_key=True)
    cash_only = Column(Boolean)
    open_package = Column(Boolean)
    min_rating = Column(Float)
    max_price = Column(Integer, nullable=True, default=None)
    user_id = Column(Integer, ForeignKey('users.id'))
