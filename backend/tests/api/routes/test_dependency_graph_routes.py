from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import UUID

import pytest

from app.api.routes import dependency_graph


@pytest.mark.asyncio
async def test_get_file_dependencies_endpoint_success(monkeypatch):
    """Returns direct and transitive dependencies and dependents."""
    file_id = UUID("12345678-1234-5678-1234-567812345678")

    file = SimpleNamespace(
        id=file_id,
        path="src/main.py",
    )
    direct_dependency = SimpleNamespace(path="src/helpers.py")
    transitive_dependency = SimpleNamespace(path="src/config.py")
    direct_dependent = SimpleNamespace(path="src/cli.py")
    transitive_dependent = SimpleNamespace(path="src/app.py")

    monkeypatch.setattr(
        dependency_graph,
        "get_file_dependency_details",
        AsyncMock(
            return_value={
                "file": file,
                "dependencies": [direct_dependency],
                "transitive_dependencies": [
                    direct_dependency,
                    transitive_dependency,
                ],
                "dependents": [direct_dependent],
                "transitive_dependents": [
                    direct_dependent,
                    transitive_dependent,
                ],
            },
        ),
    )

    response = await dependency_graph.get_file_dependencies(
        file_id=file_id,
        session=AsyncMock(),
    )

    assert response.model_dump(mode="json") == {
        "file_id": str(file_id),
        "path": "src/main.py",
        "dependencies": ["src/helpers.py"],
        "transitive_dependencies": [
            "src/helpers.py",
            "src/config.py",
        ],
        "dependents": ["src/cli.py"],
        "transitive_dependents": [
            "src/cli.py",
            "src/app.py",
        ],
    }


@pytest.mark.asyncio
async def test_get_file_dependencies_returns_404_when_file_not_found(
    client,
    monkeypatch,
):
    """Returns 404 when the requested repository file does not exist."""
    file_id = UUID("12345678-1234-5678-1234-567812345678")

    monkeypatch.setattr(
        dependency_graph,
        "get_file_dependency_details",
        AsyncMock(return_value=None),
    )

    response = await client.get(f"/api/v1/repositories/files/{file_id}/dependencies")

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Repository file not found.",
    }


@pytest.mark.asyncio
async def test_get_file_dependencies_returns_200_with_dependency_details(
    client,
    monkeypatch,
):
    """Returns dependency details through the HTTP API."""
    file_id = UUID("12345678-1234-5678-1234-567812345678")

    file = SimpleNamespace(
        id=file_id,
        path="src/main.py",
    )
    direct_dependency = SimpleNamespace(path="src/helpers.py")
    transitive_dependency = SimpleNamespace(path="src/config.py")
    direct_dependent = SimpleNamespace(path="src/cli.py")
    transitive_dependent = SimpleNamespace(path="src/app.py")

    monkeypatch.setattr(
        dependency_graph,
        "get_file_dependency_details",
        AsyncMock(
            return_value={
                "file": file,
                "dependencies": [direct_dependency],
                "transitive_dependencies": [
                    direct_dependency,
                    transitive_dependency,
                ],
                "dependents": [direct_dependent],
                "transitive_dependents": [
                    direct_dependent,
                    transitive_dependent,
                ],
            },
        ),
    )

    response = await client.get(f"/api/v1/repositories/files/{file_id}/dependencies")

    assert response.status_code == 200
    assert response.json() == {
        "file_id": str(file_id),
        "path": "src/main.py",
        "dependencies": ["src/helpers.py"],
        "transitive_dependencies": [
            "src/helpers.py",
            "src/config.py",
        ],
        "dependents": ["src/cli.py"],
        "transitive_dependents": [
            "src/cli.py",
            "src/app.py",
        ],
    }
