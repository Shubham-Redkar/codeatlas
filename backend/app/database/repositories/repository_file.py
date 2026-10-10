from pathlib import Path
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...ingestion import detect_language
from ..models import RepositoryFile


async def get_indexed_files(
    session: AsyncSession,
    repository_id: UUID,
) -> dict[str, str]:
    """
    Get indexed file paths and content hashes for a repository.
    """
    result = await session.execute(
        select(
            RepositoryFile.path,
            RepositoryFile.content_hash,
        ).where(
            RepositoryFile.repository_id == repository_id,
        )
    )

    return {row.path: row.content_hash for row in result}


async def _get_repository_file(
    session: AsyncSession,
    repository_id: UUID,
    path: str,
) -> RepositoryFile | None:
    """Get a repository file by repository ID and path."""
    result = await session.execute(
        select(RepositoryFile).where(
            RepositoryFile.repository_id == repository_id,
            RepositoryFile.path == path,
        )
    )

    return result.scalar_one_or_none()


async def create_repository_file(
    session: AsyncSession,
    repository_id: UUID,
    path: str,
    content_hash: str,
    size_bytes: int,
) -> RepositoryFile:
    """
    Create a repository file record.
    """
    repository_file = RepositoryFile(
        repository_id=repository_id,
        path=path,
        content_hash=content_hash,
        size_bytes=size_bytes,
        language=detect_language(Path(path)),
    )

    session.add(repository_file)
    await session.flush()

    return repository_file


async def update_repository_file(
    session: AsyncSession,
    repository_id: UUID,
    path: str,
    content_hash: str,
    size_bytes: int,
) -> RepositoryFile | None:
    """
    Update an existing repository file record.
    """
    repository_file = await _get_repository_file(
        session=session,
        repository_id=repository_id,
        path=path,
    )

    if repository_file is None:
        return None

    repository_file.content_hash = content_hash
    repository_file.size_bytes = size_bytes
    repository_file.language = detect_language(Path(path))

    await session.flush()

    return repository_file


async def delete_repository_file(
    session: AsyncSession,
    repository_id: UUID,
    path: str,
) -> bool:
    """
    Delete a repository file record.

    Returns True if a record was deleted, otherwise False.
    """
    repository_file = await _get_repository_file(
        session=session,
        repository_id=repository_id,
        path=path,
    )

    if repository_file is None:
        return False

    await session.delete(repository_file)
    await session.flush()

    return True
