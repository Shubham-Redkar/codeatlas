import logging

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.api.exception_handlers import register_exception_handlers
from app.core.exceptions import CodeAtlasError, GitCloneError


@pytest.fixture
def app():
    application = FastAPI()
    register_exception_handlers(application)

    @application.get("/git-error")
    async def git_error():
        raise GitCloneError("Git clone failed")

    @application.get("/app-error")
    async def app_error():
        raise CodeAtlasError("Repository not found")

    @application.get("/unexpected-error")
    async def unexpected_error():
        raise RuntimeError("Unexpected failure")

    return application


@pytest_asyncio.fixture
async def client(app: FastAPI):
    transport = ASGITransport(
        app=app,
        raise_app_exceptions=False,
    )

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as ac:
        yield ac


@pytest.mark.asyncio
async def test_git_clone_error_handler(client: AsyncClient, caplog):
    with caplog.at_level(logging.WARNING):
        response = await client.get("/git-error")

    assert response.status_code == 400
    assert response.json() == {
        "detail": "Failed to clone repository.",
        "code": "GIT_CLONE_ERROR",
    }
    assert "Git clone failed" in caplog.text
    assert "GET" in caplog.text
    assert "/git-error" in caplog.text


@pytest.mark.asyncio
async def test_code_atlas_error_handler(client: AsyncClient, caplog):
    with caplog.at_level(logging.WARNING):
        response = await client.get("/app-error")

    assert response.status_code == 400
    assert response.json() == {
        "detail": "Repository not found",
        "code": "CODE_ATLAS_ERROR",
    }
    assert "Application error" in caplog.text
    assert "CodeAtlasError" in caplog.text
    assert "/app-error" in caplog.text


@pytest.mark.asyncio
async def test_unexpected_error_handler(client: AsyncClient, caplog):
    with caplog.at_level(logging.ERROR):
        response = await client.get("/unexpected-error")

    assert response.status_code == 500
    assert response.json() == {
        "detail": "An unexpected internal server error occurred.",
        "code": "INTERNAL_SERVER_ERROR",
    }
    assert "Unhandled exception" in caplog.text
    assert "GET" in caplog.text
    assert "/unexpected-error" in caplog.text
    assert "Unexpected failure" in caplog.text
