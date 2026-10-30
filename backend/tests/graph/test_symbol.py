from uuid import UUID

from app.graph.symbol import (
    SymbolEdge,
    build_symbol_graph,
)


def test_symbol_graph_returns_direct_outgoing_and_incoming_edges() -> None:
    caller_id = UUID("00000000-0000-0000-0000-000000000001")
    callee_id = UUID("00000000-0000-0000-0000-000000000002")
    other_id = UUID("00000000-0000-0000-0000-000000000003")

    graph = build_symbol_graph(
        [
            SymbolEdge(caller_id, callee_id, "calls"),
            SymbolEdge(other_id, callee_id, "calls"),
        ]
    )

    assert graph.get_relationships(caller_id, "calls") == frozenset({callee_id})
    assert graph.get_related_symbols(callee_id, "calls") == frozenset({caller_id, other_id})


def test_symbol_graph_traversal_is_transitive_and_cycle_safe() -> None:
    first_id = UUID("00000000-0000-0000-0000-000000000001")
    second_id = UUID("00000000-0000-0000-0000-000000000002")
    third_id = UUID("00000000-0000-0000-0000-000000000003")

    graph = build_symbol_graph(
        [
            SymbolEdge(first_id, second_id, "calls"),
            SymbolEdge(second_id, third_id, "calls"),
            SymbolEdge(third_id, first_id, "calls"),
        ]
    )

    assert graph.get_transitive_relationships(first_id, "calls") == frozenset({second_id, third_id})
    assert first_id not in graph.get_transitive_relationships(
        first_id,
        "calls",
    )


def test_symbol_graph_traversal_filters_by_relationship_kind() -> None:
    first_id = UUID("00000000-0000-0000-0000-000000000001")
    second_id = UUID("00000000-0000-0000-0000-000000000002")
    third_id = UUID("00000000-0000-0000-0000-000000000003")

    graph = build_symbol_graph(
        [
            SymbolEdge(first_id, second_id, "calls"),
            SymbolEdge(second_id, third_id, "contains"),
        ]
    )

    assert graph.get_transitive_relationships(first_id, "calls") == frozenset({second_id})


def test_symbol_graph_finds_transitive_callers() -> None:
    caller_id = UUID("00000000-0000-0000-0000-000000000001")
    middle_id = UUID("00000000-0000-0000-0000-000000000002")
    changed_id = UUID("00000000-0000-0000-0000-000000000003")

    graph = build_symbol_graph(
        [
            SymbolEdge(caller_id, middle_id, "calls"),
            SymbolEdge(middle_id, changed_id, "calls"),
        ]
    )

    assert graph.get_transitive_dependents(
        changed_id,
        "calls",
    ) == frozenset({caller_id, middle_id})
