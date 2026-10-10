from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from ..database.models import Repository
from ..database.repositories import (
    create_repository_file,
    delete_repository_file,
    get_indexed_files,
    replace_symbols,
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
from ..parser import SupportedLanguage, extract_symbols, parse_source


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
            match change.change_type:
                case FileChangeType.NEW | FileChangeType.CHANGED:
                    file_path = repository_path / change.path
                    size_bytes = file_path.stat().st_size
                    content_hash = current_files[change.path]

                    if change.change_type is FileChangeType.NEW:
                        repository_file = await create_repository_file(
                            session=session,
                            repository_id=repository.id,
                            path=change.path,
                            content_hash=content_hash,
                            size_bytes=size_bytes,
                        )
                    else:
                        repository_file = await update_repository_file(
                            session=session,
                            repository_id=repository.id,
                            path=change.path,
                            content_hash=content_hash,
                            size_bytes=size_bytes,
                        )

                    if repository_file is None or repository_file.language is None:
                        continue

                    language = SupportedLanguage(repository_file.language)
                    source = file_path.read_bytes()
                    tree = parse_source(source, language)
                    symbols = extract_symbols(tree.root_node, language.value)

                    await replace_symbols(
                        session=session,
                        repository_file_id=repository_file.id,
                        symbols=symbols,
                    )

                case FileChangeType.DELETED:
                    await delete_repository_file(
                        session=session,
                        repository_id=repository.id,
                        path=change.path,
                    )

                case FileChangeType.UNCHANGED:
                    pass

    return changes
