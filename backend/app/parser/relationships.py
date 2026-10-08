from dataclasses import dataclass
from enum import StrEnum

from tree_sitter import Node


class RelationshipKind(StrEnum):
    """Kinds of relationships between symbols."""

    CONTAINS = "contains"


@dataclass(frozen=True, slots=True)
class Relationship:
    """A relationship between two symbols."""

    source: str
    target: str
    kind: RelationshipKind


def extract_relationships(
    node: Node,
    language: str,
) -> list[Relationship]:
    """
    Extract containment relationships between symbols.
    """
    relationships: list[Relationship] = []

    symbol_node_types = {
        "python": {
            "class_definition",
            "function_definition",
        },
        "javascript": {
            "class_declaration",
            "function_declaration",
            "method_definition",
        },
    }

    supported_node_types = symbol_node_types[language]

    def visit(
        current: Node,
        parent_symbol: str | None = None,
    ) -> None:
        current_symbol: str | None = None

        if current.type in supported_node_types:
            name_node = current.child_by_field_name("name")

            if name_node is not None:
                current_symbol = name_node.text.decode()

                if parent_symbol is not None:
                    relationships.append(
                        Relationship(
                            source=parent_symbol,
                            target=current_symbol,
                            kind=RelationshipKind.CONTAINS,
                        )
                    )

        for child in current.children:
            visit(child, current_symbol or parent_symbol)

    for child in node.children:
        visit(child)

    return relationships
