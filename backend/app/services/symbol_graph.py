from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from ..database.repositories import get_repository_symbol_relationships
from ..graph import SymbolEdge, SymbolGraph, build_symbol_graph


async def get_repository_symbol_graph(
    session: AsyncSession,
    repository_id: UUID,
) -> SymbolGraph:
    """Build a symbol graph from persisted relationships in a repository."""
    relationships = await get_repository_symbol_relationships(
        session=session,
        repository_id=repository_id,
    )

    edges = [
        SymbolEdge(
            source=relationship.source_symbol_id,
            target=relationship.target_symbol_id,
            kind=relationship.kind,
        )
        for relationship in relationships
    ]

    return build_symbol_graph(edges)


async def get_symbol_impact(
    session: AsyncSession,
    repository_id: UUID,
    symbol_id: UUID,
) -> frozenset[UUID]:
    """Return direct and indirect callers of a symbol."""
    graph = await get_repository_symbol_graph(
        session=session,
        repository_id=repository_id,
    )

    return graph.get_transitive_dependents(
        symbol_id,
        "calls",
    )
