import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

load_dotenv(Path(__file__).parent / ".env")

_logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    _logger.critical("DATABASE_URL is missing — application cannot connect to PostgreSQL")

engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """
    Provide a SQLAlchemy database session as a FastAPI dependency.

    Opens a session before each request and guarantees closure after,
    even if an exception occurs during request handling.

    Yields:
        Active SQLAlchemy Session instance.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()