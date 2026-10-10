import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("GEMINI_API_KEY", "test-key")
os.environ.setdefault("RATELIMIT_ENABLED", "0")

from backend.database import Base, get_db
from backend.main import app
from backend.models import User, UserPreference

TEST_DATABASE_URL = "sqlite:///:memory:"

# StaticPool ensures all sessions share one in-memory connection so tables persist
engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db():
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(db):
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def user(db):
    u = User(device_id="test-device-001")
    db.add(u)
    db.commit()
    db.refresh(u)
    return u


@pytest.fixture
def user_preference(db, user):
    pref = UserPreference(
        user_id=user.id,
        cash_only=True,
        open_package=False,
        min_rating=4.0,
        max_price=1000,
        min_review_count=None,
        new_only=False,
        search_emag=True,
        search_altex=True,
    )
    db.add(pref)
    db.commit()
    db.refresh(pref)
    return pref
