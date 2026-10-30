import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import FileDependency, Repository, RepositoryFile
from app.database.repositories.file_dependency import (
    get_file_dependencies,
    get_file_dependents,
    get_repository_dependencies,
    replace_file_dependencies,
)
from app.graph import Dependency


@pytest.mark.asyncio
async def test_replace_file_dependencies(
    db_session: AsyncSession,
) -> None:
    """Persist resolved dependency edges for a repository."""
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
    db_session.add_all([main_file, helpers_file])
    await db_session.flush()

    await replace_file_dependencies(
        session=db_session,
        repository_id=repository.id,
        dependencies=[
            Dependency(
                source="src/main.py",
                target="src/helpers.py",
            ),
        ],
    )

    result = await db_session.execute(select(FileDependency))
    persisted = list(result.scalars())

    assert len(persisted) == 1
    assert persisted[0].source_file_id == main_file.id
    assert persisted[0].target_file_id == helpers_file.id


@pytest.mark.asyncio
async def test_replace_file_dependencies_removes_stale_edges(
    db_session: AsyncSession,
) -> None:
    """Remove outdated edges when replacing a repository's dependencies."""
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
    utils_file = RepositoryFile(
        repository_id=repository.id,
        path="src/utils.py",
        content_hash="utils-hash",
        size_bytes=60,
        language="python",
    )
    db_session.add_all([main_file, helpers_file, utils_file])
    await db_session.flush()

    await replace_file_dependencies(
        session=db_session,
        repository_id=repository.id,
        dependencies=[
            Dependency(source="src/main.py", target="src/helpers.py"),
        ],
    )

    await replace_file_dependencies(
        session=db_session,
        repository_id=repository.id,
        dependencies=[
            Dependency(source="src/main.py", target="src/utils.py"),
        ],
    )

    result = await db_session.execute(select(FileDependency))
    persisted = list(result.scalars())

    assert len(persisted) == 1
    assert persisted[0].source_file_id == main_file.id
    assert persisted[0].target_file_id == utils_file.id


@pytest.mark.asyncio
async def test_get_file_dependencies(
    db_session: AsyncSession,
) -> None:
    """Return files directly depended on by a repository file."""
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
    unrelated_file = RepositoryFile(
        repository_id=repository.id,
        path="src/unrelated.py",
        content_hash="unrelated-hash",
        size_bytes=50,
        language="python",
    )
    db_session.add_all([main_file, helpers_file, unrelated_file])
    await db_session.flush()

    await replace_file_dependencies(
        session=db_session,
        repository_id=repository.id,
        dependencies=[
            Dependency(source="src/main.py", target="src/helpers.py"),
        ],
    )

    result = await get_file_dependencies(
        session=db_session,
        repository_file_id=main_file.id,
    )

    assert result == [helpers_file]


@pytest.mark.asyncio
async def test_get_file_dependents(
    db_session: AsyncSession,
) -> None:
    """Return files that directly depend on a repository file."""
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
    db_session.add_all([main_file, helpers_file])
    await db_session.flush()

    await replace_file_dependencies(
        session=db_session,
        repository_id=repository.id,
        dependencies=[
            Dependency(source="src/main.py", target="src/helpers.py"),
        ],
    )

    result = await get_file_dependents(
        session=db_session,
        repository_file_id=helpers_file.id,
    )

    assert result == [main_file]


@pytest.mark.asyncio
async def test_get_repository_dependencies(
    db_session: AsyncSession,
) -> None:
    """Return all persisted dependency edges for a repository."""
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

    result = await get_repository_dependencies(
        session=db_session,
        repository_id=repository.id,
    )

    assert result == [
        Dependency(source="src/helpers.py", target="src/config.py"),
        Dependency(source="src/main.py", target="src/helpers.py"),
    ]
