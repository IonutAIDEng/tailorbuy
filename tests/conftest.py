import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("GEMINI_API_KEY", "test-key")
os.environ.setdefault("RATELIMIT_ENABLED", "0")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-32-chars-minimum!")

from backend.database import Base, get_db
from backend.dependencies import get_current_user
from backend.main import app
from backend.models import User, UserPreference
from backend.services.auth_service import hash_password

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
    u = User(
        email="test@example.com",
        hashed_password=hash_password("testpassword"),
        nickname="Tester",
    )
    db.add(u)
    db.commit()
    db.refresh(u)
    return u


@pytest.fixture
def auth_client(db, user):
    """TestClient with both get_db and get_current_user overridden for protected endpoints."""
    def override_get_db():
        try:
            yield db
        finally:
            pass

    def override_get_current_user():
        return user

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


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
