from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from .config import get_settings
from .database.session import check_database, engine

settings = get_settings()


@asynccontextmanager
async def lifespan(
    app: FastAPI,
) -> AsyncGenerator[None]:
    """
    Manage application startup and shutdown resources.
    """
    yield
    await engine.dispose()


app = FastAPI(
    title=settings.app_name,
    description="AI-powered codebase intelligence platform",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get(
    "/",
    tags=["Root"],
)
async def home() -> dict[str, str]:
    return {
        "service": "CodeAtlas API",
        "message": "API is live and ready to serve requests",
        "status": "operational",
    }


@app.get(
    "/health",
    tags=["Health"],
)
async def health_check() -> dict[str, str]:
    return {"status": "healthy"}


@app.get(
    "/health/ready",
    tags=["Health"],
)
async def readiness() -> dict[str, str]:
    await check_database()
    return {"status": "ready"}
