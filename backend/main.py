import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded

from backend.database import engine, Base
from backend import models
from backend.limiter import limiter
from backend.routers import auth, health, search, preferences

logging.basicConfig(level=logging.INFO)
_logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create database tables on startup; log shutdown on exit."""
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

app.state.limiter = limiter


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    """Convert slowapi's RateLimitExceeded into a structured 429 response."""
    return JSONResponse(
        status_code=429,
        content={"detail": {"code": "rate_limit_exceeded", "message": "Prea multe cereri. Încearcă din nou în câteva secunde."}},
    )


app.include_router(health.router)
app.include_router(auth.router)
app.include_router(search.router)
app.include_router(preferences.router)
