from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI

from app import main


@pytest.mark.asyncio
async def test_home():
    result = await main.home()

    assert result == {
        "service": "CodeAtlas API",
        "message": "API is live and ready to serve requests",
        "status": "operational",
    }


@pytest.mark.asyncio
async def test_health_check():
    result = await main.health_check()

    assert result == {"status": "healthy"}


@pytest.mark.asyncio
async def test_readiness(monkeypatch):
    check_database = AsyncMock()
    monkeypatch.setattr(main, "check_database", check_database)

    result = await main.readiness()

    assert result == {"status": "ready"}
    check_database.assert_awaited_once()


@pytest.mark.asyncio
async def test_lifespan_startup_and_shutdown(monkeypatch):
    check_database = AsyncMock()
    dispose = AsyncMock()

    mock_engine = MagicMock()
    mock_engine.dispose = dispose

    monkeypatch.setattr(main, "check_database", check_database)
    monkeypatch.setattr(main, "engine", mock_engine)

    async with main.lifespan(FastAPI()):
        check_database.assert_awaited_once()
        dispose.assert_not_awaited()

    dispose.assert_awaited_once()


@pytest.mark.asyncio
async def test_lifespan_shutdown_after_exception(monkeypatch):
    check_database = AsyncMock()
    dispose = AsyncMock()

    mock_engine = MagicMock()
    mock_engine.dispose = dispose

    monkeypatch.setattr(main, "check_database", check_database)
    monkeypatch.setattr(main, "engine", mock_engine)

    with pytest.raises(RuntimeError, match="test failure"):
        async with main.lifespan(FastAPI()):
            raise RuntimeError("test failure")

    check_database.assert_awaited_once()
    dispose.assert_awaited_once()
