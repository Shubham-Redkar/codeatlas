from collections.abc import Iterable
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import FileDependency, RepositoryFile
from app.graph import Dependency


async def replace_file_dependencies(
    session: AsyncSession,
    repository_id: UUID,
    dependencies: Iterable[Dependency],
) -> None:
    """Replace a repository's persisted dependency edges."""
    result = await session.execute(
        select(RepositoryFile.id, RepositoryFile.path).where(
            RepositoryFile.repository_id == repository_id
        )
    )
    file_ids_by_path = {path: file_id for file_id, path in result.all()}

    repository_file_ids = list(file_ids_by_path.values())

    if repository_file_ids:
        await session.execute(
            delete(FileDependency).where(FileDependency.source_file_id.in_(repository_file_ids))
        )

    edges = {
        (file_ids_by_path[dependency.source], file_ids_by_path[dependency.target])
        for dependency in dependencies
        if dependency.source in file_ids_by_path
        and dependency.target in file_ids_by_path
        and dependency.source != dependency.target
    }

    session.add_all(
        FileDependency(
            source_file_id=source_file_id,
            target_file_id=target_file_id,
        )
        for source_file_id, target_file_id in edges
    )
    await session.flush()


async def get_file_dependencies(
    session: AsyncSession,
    repository_file_id: UUID,
) -> list[RepositoryFile]:
    """Return files directly depended on by a repository file."""
    result = await session.execute(
        select(RepositoryFile)
        .join(
            FileDependency,
            FileDependency.target_file_id == RepositoryFile.id,
        )
        .where(FileDependency.source_file_id == repository_file_id)
        .order_by(RepositoryFile.path)
    )
    return list(result.scalars().all())


async def get_file_dependents(
    session: AsyncSession,
    repository_file_id: UUID,
) -> list[RepositoryFile]:
    """Return files that directly depend on a repository file."""
    result = await session.execute(
        select(RepositoryFile)
        .join(
            FileDependency,
            FileDependency.source_file_id == RepositoryFile.id,
        )
        .where(FileDependency.target_file_id == repository_file_id)
        .order_by(RepositoryFile.path)
    )
    return list(result.scalars().all())


async def get_repository_dependencies(
    session: AsyncSession,
    repository_id: UUID,
) -> list[Dependency]:
    """Return all persisted dependency edges for a repository."""
    source_file = RepositoryFile.__table__.alias("source_file")
    target_file = RepositoryFile.__table__.alias("target_file")

    result = await session.execute(
        select(source_file.c.path, target_file.c.path)
        .join(
            FileDependency,
            FileDependency.source_file_id == source_file.c.id,
        )
        .join(
            target_file,
            FileDependency.target_file_id == target_file.c.id,
        )
        .where(
            source_file.c.repository_id == repository_id,
            target_file.c.repository_id == repository_id,
        )
        .order_by(source_file.c.path, target_file.c.path)
    )

    return [
        Dependency(source=source_path, target=target_path)
        for source_path, target_path in result.all()
    ]


async def get_repository_file(
    session: AsyncSession,
    repository_file_id: UUID,
) -> RepositoryFile | None:
    """Return a repository file by ID."""
    result = await session.execute(
        select(RepositoryFile).where(RepositoryFile.id == repository_file_id)
    )
    return result.scalar_one_or_none()


async def get_repository_files_by_paths(
    session: AsyncSession,
    repository_id: UUID,
    paths: Iterable[str],
) -> list[RepositoryFile]:
    """Return repository files matching the supplied paths."""
    path_set = set(paths)
    if not path_set:
        return []

    result = await session.execute(
        select(RepositoryFile)
        .where(
            RepositoryFile.repository_id == repository_id,
            RepositoryFile.path.in_(path_set),
        )
        .order_by(RepositoryFile.path)
    )
    return list(result.scalars().all())
