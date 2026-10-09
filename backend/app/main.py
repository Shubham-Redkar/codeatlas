from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from .api.exception_handlers import register_exception_handlers
from .api.routes import api_router
from .core.config import get_settings
from .core.logging import configure_logging
from .database.session import check_database, engine

settings = get_settings()

configure_logging()


@asynccontextmanager
async def lifespan(
    app: FastAPI,
) -> AsyncGenerator[None]:
    """
    Manage application startup and shutdown resources.
    """
    await check_database()

    try:
        yield
    finally:
        await engine.dispose()


app = FastAPI(
    title=settings.app_name,
    description="AI-powered codebase intelligence platform",
    version="0.1.0",
    lifespan=lifespan,
)

register_exception_handlers(app)


@app.get(
    "/",
    tags=["Root"],
)
async def home() -> dict[str, str]:
    """Return basic API information."""
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
    """Return the application's liveness status."""
    return {
        "status": "healthy",
    }


@app.get(
    "/health/ready",
    tags=["Health"],
)
async def readiness() -> dict[str, str]:
    """Check whether the application is ready to serve requests."""
    await check_database()

    return {
        "status": "ready",
    }


app.include_router(
    api_router,
    prefix="/api/v1",
)
