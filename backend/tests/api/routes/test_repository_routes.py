from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import UUID

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from pydantic import HttpUrl
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db
from app.api.routes import repositories
from app.core.exceptions import GitCloneError
from app.main import app as fastapi_app
from app.schemas.repositories import RepositoryCreateRequest


@pytest.mark.asyncio
async def test_create_repository_success(monkeypatch):
    """Returns the created repository and indexed file count."""
    repository = SimpleNamespace(
        id=UUID("12345678-1234-5678-1234-567812345678"),
        name="example-repo",
        url=HttpUrl("https://github.com/example/example-repo"),
        branch="main",
    )
    file_count = 12

    mock_ingest = AsyncMock(return_value=(repository, file_count))
    monkeypatch.setattr(repositories, "ingest_repository", mock_ingest)

    request = RepositoryCreateRequest(
        url=HttpUrl("https://github.com/example/example-repo"),
        branch="main",
    )
    session = AsyncMock(spec=AsyncSession)

    response = await repositories.create_repository(
        request=request,
        session=session,
    )

    assert response.id == UUID("12345678-1234-5678-1234-567812345678")
    assert response.name == "example-repo"
    assert str(response.url).rstrip("/") == ("https://github.com/example/example-repo")
    assert response.branch == "main"
    assert response.file_count == 12

    mock_ingest.assert_awaited_once_with(
        session=session,
        url="https://github.com/example/example-repo",
        branch="main",
    )


@pytest.mark.asyncio
async def test_create_repository_propagates_ingestion_error(monkeypatch):
    """Propagates errors raised by the ingestion service."""
    mock_ingest = AsyncMock(
        side_effect=RuntimeError("Repository ingestion failed"),
    )
    monkeypatch.setattr(repositories, "ingest_repository", mock_ingest)

    request = RepositoryCreateRequest(
        url=HttpUrl("https://github.com/example/example-repo"),
        branch="main",
    )
    session = AsyncMock(spec=AsyncSession)

    with pytest.raises(
        RuntimeError,
        match="Repository ingestion failed",
    ):
        await repositories.create_repository(
            request=request,
            session=session,
        )

    mock_ingest.assert_awaited_once_with(
        session=session,
        url="https://github.com/example/example-repo",
        branch="main",
    )


@pytest_asyncio.fixture
async def api_client(monkeypatch):
    """Create an API client without opening a database connection."""

    async def override_get_db():
        yield None

    monkeypatch.setitem(
        fastapi_app.dependency_overrides,
        get_db,
        override_get_db,
    )

    transport = ASGITransport(
        app=fastapi_app,
        raise_app_exceptions=False,
    )

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:
        yield client


@pytest.mark.asyncio
async def test_create_repository_endpoint_success(
    api_client,
    monkeypatch,
):
    """Returns HTTP 201 with the repository and indexed file count."""
    repository = SimpleNamespace(
        id=UUID("12345678-1234-5678-1234-567812345678"),
        name="example-repo",
        url=HttpUrl("https://github.com/example/example-repo"),
        branch="main",
    )

    mock_ingest = AsyncMock(return_value=(repository, 12))
    monkeypatch.setattr(
        repositories,
        "ingest_repository",
        mock_ingest,
    )

    response = await api_client.post(
        "/api/v1/repositories",
        json={
            "url": "https://github.com/example/example-repo",
            "branch": "main",
        },
    )

    assert response.status_code == 201
    assert response.json() == {
        "id": "12345678-1234-5678-1234-567812345678",
        "name": "example-repo",
        "url": "https://github.com/example/example-repo",
        "branch": "main",
        "file_count": 12,
    }

    mock_ingest.assert_awaited_once()


@pytest.mark.asyncio
async def test_create_repository_endpoint_invalid_url(
    api_client,
    monkeypatch,
):
    """Returns HTTP 422 without invoking ingestion for an invalid URL."""
    mock_ingest = AsyncMock()
    monkeypatch.setattr(
        repositories,
        "ingest_repository",
        mock_ingest,
    )

    response = await api_client.post(
        "/api/v1/repositories",
        json={"url": "not-a-url"},
    )

    assert response.status_code == 422
    assert response.json()["detail"]
    mock_ingest.assert_not_awaited()


@pytest.mark.asyncio
async def test_create_repository_endpoint_git_clone_failure(
    api_client,
    monkeypatch,
):
    """Returns HTTP 400 when Git cloning fails."""
    mock_ingest = AsyncMock(
        side_effect=GitCloneError("clone failed"),
    )
    monkeypatch.setattr(
        repositories,
        "ingest_repository",
        mock_ingest,
    )

    response = await api_client.post(
        "/api/v1/repositories",
        json={
            "url": "https://github.com/example/example-repo",
            "branch": "main",
        },
    )

    assert response.status_code == 400
    assert response.json() == {
        "detail": "Failed to clone repository.",
        "code": "GIT_CLONE_ERROR",
    }

    mock_ingest.assert_awaited_once()
