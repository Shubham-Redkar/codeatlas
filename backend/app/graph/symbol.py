from collections import defaultdict, deque
from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True, slots=True)
class SymbolEdge:
    source: UUID
    target: UUID
    kind: str


@dataclass(frozen=True, slots=True)
class SymbolGraph:
    edges: tuple[SymbolEdge, ...]

    def get_relationships(
        self,
        symbol_id: UUID,
        kind: str,
    ) -> frozenset[UUID]:
        """Return symbols directly reached by outgoing relationships."""
        return frozenset(
            edge.target for edge in self.edges if edge.source == symbol_id and edge.kind == kind
        )

    def get_related_symbols(
        self,
        symbol_id: UUID,
        kind: str,
    ) -> frozenset[UUID]:
        """Return symbols with incoming relationships to this symbol."""
        return frozenset(
            edge.source for edge in self.edges if edge.target == symbol_id and edge.kind == kind
        )

    def get_transitive_relationships(
        self,
        symbol_id: UUID,
        kind: str,
    ) -> frozenset[UUID]:
        """Return all reachable symbols, excluding the starting symbol."""
        adjacency: dict[UUID, set[UUID]] = defaultdict(set)
        for edge in self.edges:
            if edge.kind == kind:
                adjacency[edge.source].add(edge.target)

        visited: set[UUID] = set()
        pending = deque(adjacency[symbol_id])

        while pending:
            current = pending.popleft()
            if current == symbol_id or current in visited:
                continue

            visited.add(current)
            pending.extend(adjacency[current] - visited)

        return frozenset(visited)

    def get_transitive_dependents(
        self,
        symbol_id: UUID,
        kind: str,
    ) -> frozenset[UUID]:
        """Return all symbols that transitively lead to this symbol."""
        reverse_adjacency: dict[UUID, set[UUID]] = defaultdict(set)

        for edge in self.edges:
            if edge.kind == kind:
                reverse_adjacency[edge.target].add(edge.source)

        visited: set[UUID] = set()
        pending = deque(reverse_adjacency[symbol_id])

        while pending:
            current = pending.popleft()
            if current == symbol_id or current in visited:
                continue

            visited.add(current)
            pending.extend(reverse_adjacency[current] - visited)

        return frozenset(visited)


def build_symbol_graph(
    edges: list[SymbolEdge],
) -> SymbolGraph:
    """Build an immutable symbol graph from relationship edges."""
    return SymbolGraph(edges=tuple(edges))
