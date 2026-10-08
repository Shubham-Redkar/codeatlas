from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from ..database.models import Repository
from ..database.repositories.repository_file import (
    create_repository_file,
    delete_repository_file,
    get_indexed_files,
    update_repository_file,
)
from ..ingestion.files import discover_files
from ..ingestion.filters import filter_files
from ..ingestion.indexing import (
    FileChange,
    FileChangeType,
    build_current_file_state,
    compare_files,
)


async def index_repository(
    session: AsyncSession,
    repository: Repository,
    repository_path: Path,
) -> list[FileChange]:
    """
    Synchronize repository file state with the database.
    """
    discovered_files = discover_files(repository_path)
    filtered_files = filter_files(discovered_files)

    current_files = build_current_file_state(
        repository_path=repository_path,
        files=filtered_files,
    )

    async with session.begin():
        indexed_files = await get_indexed_files(
            session=session,
            repository_id=repository.id,
        )

        changes = compare_files(
            current_files=current_files,
            indexed_files=indexed_files,
        )

        for change in changes:
            file_path = repository_path / change.path

            if change.change_type is FileChangeType.NEW:
                await create_repository_file(
                    session=session,
                    repository_id=repository.id,
                    path=change.path,
                    content_hash=current_files[change.path],
                    size_bytes=file_path.stat().st_size,
                )

            elif change.change_type is FileChangeType.CHANGED:
                await update_repository_file(
                    session=session,
                    repository_id=repository.id,
                    path=change.path,
                    content_hash=current_files[change.path],
                    size_bytes=file_path.stat().st_size,
                )

            elif change.change_type is FileChangeType.DELETED:
                await delete_repository_file(
                    session=session,
                    repository_id=repository.id,
                    path=change.path,
                )

    return changes
