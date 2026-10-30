from collections.abc import Iterable
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import RepositoryFile, Symbol, SymbolRelationship

SymbolRelationshipInput = tuple[UUID, UUID, str, int | None]


async def replace_symbol_relationships(
    session: AsyncSession,
    repository_file_id: UUID,
    relationships: Iterable[SymbolRelationshipInput],
) -> None:
    """Replace persisted symbol relationships with the supplied edges."""
    result = await session.execute(
        select(Symbol.id).where(
            Symbol.repository_file_id == repository_file_id,
        )
    )
    source_symbol_ids = set(result.scalars().all())

    if source_symbol_ids:
        await session.execute(
            delete(SymbolRelationship).where(
                SymbolRelationship.source_symbol_id.in_(source_symbol_ids),
            )
        )

    edges = {
        (source_id, target_id, kind, line)
        for source_id, target_id, kind, line in relationships
        if source_id in source_symbol_ids and source_id != target_id
    }

    session.add_all(
        SymbolRelationship(
            source_symbol_id=source_id,
            target_symbol_id=target_id,
            kind=kind,
            line=line,
        )
        for source_id, target_id, kind, line in edges
    )
    await session.flush()


async def get_repository_symbol_relationships(
    session: AsyncSession,
    repository_id: UUID,
) -> list[SymbolRelationship]:
    """Return symbol relationships originating in a repository."""
    source_file_ids = select(RepositoryFile.id).where(
        RepositoryFile.repository_id == repository_id,
    )
    target_file_ids = select(RepositoryFile.id).where(
        RepositoryFile.repository_id == repository_id,
    )

    result = await session.execute(
        select(SymbolRelationship)
        .join(
            Symbol,
            SymbolRelationship.source_symbol_id == Symbol.id,
        )
        .where(Symbol.repository_file_id.in_(source_file_ids))
        .where(
            SymbolRelationship.target_symbol_id.in_(
                select(Symbol.id).where(Symbol.repository_file_id.in_(target_file_ids))
            )
        )
    )

    return list(result.scalars().all())
