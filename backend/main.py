from contextlib import asynccontextmanager

from fastapi import FastAPI

from backend.database import engine, Base
from backend import models  # noqa: F401
from backend.routers import health


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="TailorBuy API",
    description="API pentru găsirea produselor pe site-uri de e-commerce din România",
    version="0.1.0",
    lifespan=lifespan
)

app.include_router(health.router)