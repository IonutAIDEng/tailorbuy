import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from backend.database import engine, Base
from backend import models
from backend.routers import health, search, preferences

logging.basicConfig(level=logging.INFO)
_logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    _logger.info("Application starting — creating database tables if needed")
    Base.metadata.create_all(bind=engine)
    _logger.info("Database tables ready")
    yield
    _logger.info("Application shutting down")


app = FastAPI(
    title="TailorBuy API",
    description="API pentru găsirea produselor pe site-uri de e-commerce din România",
    version="0.1.0",
    lifespan=lifespan
)

app.include_router(health.router)
app.include_router(search.router)
app.include_router(preferences.router)