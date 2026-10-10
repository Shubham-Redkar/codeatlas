from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import Repository, RepositoryFile
from app.database.repositories.repository_file import (
    create_repository_file,
    delete_repository_file,
    get_indexed_files,
    update_repository_file,
)
from app.ingestion import DetectedLanguage


@pytest.mark.asyncio
async def test_get_indexed_files(
    db_session: AsyncSession,
) -> None:
    repository = Repository(
        name="CodeAtlas",
        url="https://github.com/example/codeatlas.git",
        branch="main",
    )

    other_repository = Repository(
        name="Other",
        url="https://github.com/example/other.git",
        branch="main",
    )

    db_session.add_all([repository, other_repository])
    await db_session.flush()

    first_file = RepositoryFile(
        repository_id=repository.id,
        path="src/main.py",
        content_hash="abc123",
        size_bytes=100,
    )

    second_file = RepositoryFile(
        repository_id=repository.id,
        path="README.md",
        content_hash="def456",
        size_bytes=50,
    )

    other_repository_file = RepositoryFile(
        repository_id=other_repository.id,
        path="src/other.py",
        content_hash="xyz789",
        size_bytes=75,
    )

    db_session.add_all([first_file, second_file, other_repository_file])
    await db_session.flush()

    indexed_files = await get_indexed_files(
        session=db_session,
        repository_id=repository.id,
    )

    assert indexed_files == {
        "src/main.py": "abc123",
        "README.md": "def456",
    }


@pytest.mark.asyncio
async def test_create_repository_file(
    db_session: AsyncSession,
) -> None:
    repository = Repository(
        name="CodeAtlas",
        url="https://github.com/example/codeatlas.git",
        branch="main",
    )

    db_session.add(repository)
    await db_session.flush()

    repository_file = await create_repository_file(
        session=db_session,
        repository_id=repository.id,
        path="src/main.py",
        content_hash="abc123",
        size_bytes=128,
    )

    assert repository_file.id is not None
    assert repository_file.repository_id == repository.id
    assert repository_file.path == "src/main.py"
    assert repository_file.content_hash == "abc123"
    assert repository_file.size_bytes == 128
    assert repository_file.language == DetectedLanguage.PYTHON
    assert repository_file.created_at is not None
    assert repository_file.updated_at is not None


@pytest.mark.asyncio
async def test_create_repository_file_unknown_language(
    db_session: AsyncSession,
) -> None:
    repository = Repository(
        name="CodeAtlas",
        url="https://github.com/example/codeatlas.git",
        branch="main",
    )

    db_session.add(repository)
    await db_session.flush()

    repository_file = await create_repository_file(
        session=db_session,
        repository_id=repository.id,
        path="assets/data.unknownext",
        content_hash="abc123",
        size_bytes=32,
    )

    assert repository_file.path == "assets/data.unknownext"
    assert repository_file.language is None


@pytest.mark.asyncio
async def test_update_repository_file(
    db_session: AsyncSession,
) -> None:
    repository = Repository(
        name="CodeAtlas",
        url="https://github.com/example/codeatlas.git",
        branch="main",
    )

    db_session.add(repository)
    await db_session.flush()

    repository_file = await create_repository_file(
        session=db_session,
        repository_id=repository.id,
        path="src/main.py",
        content_hash="old-hash",
        size_bytes=100,
    )

    file_id = repository_file.id

    updated_file = await update_repository_file(
        session=db_session,
        repository_id=repository.id,
        path="src/main.py",
        content_hash="new-hash",
        size_bytes=250,
    )

    assert updated_file is not None
    assert updated_file.id == file_id
    assert updated_file.repository_id == repository.id
    assert updated_file.path == "src/main.py"
    assert updated_file.content_hash == "new-hash"
    assert updated_file.size_bytes == 250
    assert updated_file.language == DetectedLanguage.PYTHON


@pytest.mark.asyncio
async def test_update_repository_file_not_found(
    db_session: AsyncSession,
) -> None:
    updated_file = await update_repository_file(
        session=db_session,
        repository_id=uuid4(),
        path="src/missing.py",
        content_hash="new-hash",
        size_bytes=100,
    )

    assert updated_file is None


@pytest.mark.asyncio
async def test_update_repository_file_refreshes_language(
    db_session: AsyncSession,
) -> None:
    repository = Repository(
        name="CodeAtlas",
        url="https://github.com/example/codeatlas.git",
        branch="main",
    )

    db_session.add(repository)
    await db_session.flush()

    repository_file = await create_repository_file(
        session=db_session,
        repository_id=repository.id,
        path="src/main.py",
        content_hash="old-hash",
        size_bytes=100,
    )

    file_id = repository_file.id

    updated_file = await update_repository_file(
        session=db_session,
        repository_id=repository.id,
        path="src/main.py",
        content_hash="new-hash",
        size_bytes=200,
    )

    assert updated_file is not None
    assert updated_file.id == file_id
    assert updated_file.language == DetectedLanguage.PYTHON
    assert updated_file.content_hash == "new-hash"
    assert updated_file.size_bytes == 200


@pytest.mark.asyncio
async def test_delete_repository_file(
    db_session: AsyncSession,
) -> None:
    repository = Repository(
        name="CodeAtlas",
        url="https://github.com/example/codeatlas.git",
        branch="main",
    )

    db_session.add(repository)
    await db_session.flush()

    await create_repository_file(
        session=db_session,
        repository_id=repository.id,
        path="src/main.py",
        content_hash="abc123",
        size_bytes=100,
    )

    deleted = await delete_repository_file(
        session=db_session,
        repository_id=repository.id,
        path="src/main.py",
    )

    assert deleted is True

    indexed_files = await get_indexed_files(
        session=db_session,
        repository_id=repository.id,
    )

    assert indexed_files == {}


@pytest.mark.asyncio
async def test_delete_repository_file_not_found(
    db_session: AsyncSession,
) -> None:
    deleted = await delete_repository_file(
        session=db_session,
        repository_id=uuid4(),
        path="does/not/exist.py",
    )

    assert deleted is False
