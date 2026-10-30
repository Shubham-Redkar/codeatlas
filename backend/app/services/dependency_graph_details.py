from typing import TypedDict
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from ..database.models import RepositoryFile
from ..database.repositories import (
    get_file_dependencies,
    get_file_dependents,
    get_repository_file,
)
from .dependency_graph import (
    get_transitive_dependencies,
    get_transitive_dependents,
)


class FileDependencyDetails(TypedDict):
    """Represent a file and its dependency relationships."""

    file: RepositoryFile
    dependencies: list[RepositoryFile]
    transitive_dependencies: list[RepositoryFile]
    dependents: list[RepositoryFile]
    transitive_dependents: list[RepositoryFile]


async def get_file_dependency_details(
    session: AsyncSession,
    repository_file_id: UUID,
) -> FileDependencyDetails | None:
    """Return a file and its direct and transitive dependency relationships."""
    repository_file = await get_repository_file(
        session=session,
        repository_file_id=repository_file_id,
    )
    if repository_file is None:
        return None

    dependencies = await get_file_dependencies(
        session=session,
        repository_file_id=repository_file_id,
    )
    dependents = await get_file_dependents(
        session=session,
        repository_file_id=repository_file_id,
    )
    transitive_dependencies = await get_transitive_dependencies(
        session=session,
        repository_file_id=repository_file_id,
    )
    transitive_dependents = await get_transitive_dependents(
        session=session,
        repository_file_id=repository_file_id,
    )

    return {
        "file": repository_file,
        "dependencies": dependencies,
        "transitive_dependencies": transitive_dependencies,
        "dependents": dependents,
        "transitive_dependents": transitive_dependents,
    }
