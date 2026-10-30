import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import Repository, RepositoryFile
from app.database.repositories.file_dependency import replace_file_dependencies
from app.graph import Dependency
from app.services.dependency_graph import get_transitive_dependencies, get_transitive_dependents


@pytest.mark.asyncio
async def test_get_transitive_dependencies(
    db_session: AsyncSession,
) -> None:
    """Return direct and indirect dependencies of a repository file."""
    repository = Repository(
        name="CodeAtlas",
        url="https://github.com/example/codeatlas.git",
        branch="main",
    )
    db_session.add(repository)
    await db_session.flush()

    main_file = RepositoryFile(
        repository_id=repository.id,
        path="src/main.py",
        content_hash="main-hash",
        size_bytes=100,
        language="python",
    )
    helpers_file = RepositoryFile(
        repository_id=repository.id,
        path="src/helpers.py",
        content_hash="helpers-hash",
        size_bytes=80,
        language="python",
    )
    config_file = RepositoryFile(
        repository_id=repository.id,
        path="src/config.py",
        content_hash="config-hash",
        size_bytes=60,
        language="python",
    )
    db_session.add_all([main_file, helpers_file, config_file])
    await db_session.flush()

    await replace_file_dependencies(
        session=db_session,
        repository_id=repository.id,
        dependencies=[
            Dependency(source="src/main.py", target="src/helpers.py"),
            Dependency(source="src/helpers.py", target="src/config.py"),
        ],
    )

    result = await get_transitive_dependencies(
        session=db_session,
        repository_file_id=main_file.id,
    )

    assert result == [config_file, helpers_file]


@pytest.mark.asyncio
async def test_get_transitive_dependents(
    db_session: AsyncSession,
) -> None:
    """Return direct and indirect dependents of a repository file."""
    repository = Repository(
        name="CodeAtlas",
        url="https://github.com/example/codeatlas.git",
        branch="main",
    )
    db_session.add(repository)
    await db_session.flush()

    main_file = RepositoryFile(
        repository_id=repository.id,
        path="src/main.py",
        content_hash="main-hash",
        size_bytes=100,
        language="python",
    )
    helpers_file = RepositoryFile(
        repository_id=repository.id,
        path="src/helpers.py",
        content_hash="helpers-hash",
        size_bytes=80,
        language="python",
    )
    config_file = RepositoryFile(
        repository_id=repository.id,
        path="src/config.py",
        content_hash="config-hash",
        size_bytes=60,
        language="python",
    )
    db_session.add_all([main_file, helpers_file, config_file])
    await db_session.flush()

    await replace_file_dependencies(
        session=db_session,
        repository_id=repository.id,
        dependencies=[
            Dependency(source="src/main.py", target="src/helpers.py"),
            Dependency(source="src/helpers.py", target="src/config.py"),
        ],
    )

    result = await get_transitive_dependents(
        session=db_session,
        repository_file_id=config_file.id,
    )

    assert result == [helpers_file, main_file]


@pytest.mark.asyncio
async def test_get_transitive_dependencies_handles_cycles(
    db_session: AsyncSession,
) -> None:
    """Handle cyclic dependency edges without returning the source file."""
    repository = Repository(
        name="CodeAtlas",
        url="https://github.com/example/codeatlas.git",
        branch="main",
    )
    db_session.add(repository)
    await db_session.flush()

    main_file = RepositoryFile(
        repository_id=repository.id,
        path="src/main.py",
        content_hash="main-hash",
        size_bytes=100,
        language="python",
    )
    helpers_file = RepositoryFile(
        repository_id=repository.id,
        path="src/helpers.py",
        content_hash="helpers-hash",
        size_bytes=80,
        language="python",
    )
    config_file = RepositoryFile(
        repository_id=repository.id,
        path="src/config.py",
        content_hash="config-hash",
        size_bytes=60,
        language="python",
    )
    db_session.add_all([main_file, helpers_file, config_file])
    await db_session.flush()

    await replace_file_dependencies(
        session=db_session,
        repository_id=repository.id,
        dependencies=[
            Dependency(source="src/main.py", target="src/helpers.py"),
            Dependency(source="src/helpers.py", target="src/config.py"),
            Dependency(source="src/config.py", target="src/main.py"),
        ],
    )

    result = await get_transitive_dependencies(
        session=db_session,
        repository_file_id=main_file.id,
    )

    assert result == [config_file, helpers_file]
