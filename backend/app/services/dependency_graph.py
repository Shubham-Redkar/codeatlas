from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from ..database.models import RepositoryFile
from ..database.repositories import (
    get_repository_dependencies,
    get_repository_file,
    get_repository_files_by_paths,
)
from ..graph import build_dependency_graph


async def get_transitive_dependencies(
    session: AsyncSession,
    repository_file_id: UUID,
) -> list[RepositoryFile]:
    """Return direct and indirect dependencies of a repository file."""
    source_file = await get_repository_file(session, repository_file_id)
    if source_file is None:
        return []

    dependencies = await get_repository_dependencies(
        session=session,
        repository_id=source_file.repository_id,
    )
    graph = build_dependency_graph(dependencies)
    dependency_paths = graph.get_transitive_dependencies(source_file.path)

    return await get_repository_files_by_paths(
        session=session,
        repository_id=source_file.repository_id,
        paths=dependency_paths,
    )


async def get_transitive_dependents(
    session: AsyncSession,
    repository_file_id: UUID,
) -> list[RepositoryFile]:
    """Return direct and indirect dependents of a repository file."""
    target_file = await get_repository_file(session, repository_file_id)
    if target_file is None:
        return []

    dependencies = await get_repository_dependencies(
        session=session,
        repository_id=target_file.repository_id,
    )
    graph = build_dependency_graph(dependencies)
    dependent_paths = graph.get_transitive_dependents(target_file.path)

    return await get_repository_files_by_paths(
        session=session,
        repository_id=target_file.repository_id,
        paths=dependent_paths,
    )
