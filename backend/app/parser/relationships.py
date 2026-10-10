from dataclasses import dataclass
from enum import StrEnum

from tree_sitter import Node

from ..core.exceptions import UnsupportedLanguageError


class RelationshipKind(StrEnum):
    """Kinds of relationships between symbols."""

    CONTAINS = "contains"
    CALLS = "calls"


@dataclass(frozen=True, slots=True)
class Relationship:
    """A relationship between two symbols, optionally tied to a source line."""

    source: str
    target: str
    kind: RelationshipKind
    line: int | None = None


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
        "typescript": {
            "class_declaration",
            "function_declaration",
            "method_definition",
        },
    }
    call_node_types = {
        "python": {"call"},
        "javascript": {"call_expression"},
        "typescript": {"call_expression"},
    }

    try:
        supported_symbol_types = symbol_node_types[language]
        supported_call_types = call_node_types[language]
    except KeyError as exc:
        raise UnsupportedLanguageError(
            f"Unsupported language: {language}",
        ) from exc

    def get_symbol_name(current: Node) -> str | None:
        """
        Return the declared name of a function or class node.
        """
        name_node = current.child_by_field_name("name")
        if name_node is None or name_node.text is None:
            return None
        return name_node.text.decode()

    def get_call_name(current: Node) -> str | None:
        """
        Return a readable callee name from a call-expression node.
        """
        function_node = current.child_by_field_name("function")
        if function_node is None:
            return None

        if (
            function_node.type in {"identifier", "attribute", "member_expression"}
            and function_node.text is not None
        ):
            return function_node.text.decode()

        return None

    def visit(
        current: Node,
        parent_symbol: str | None = None,
    ) -> None:
        """
        Recursively traverse the syntax tree and record symbol containment.
        """
        current_symbol = (
            get_symbol_name(current) if current.type in supported_symbol_types else None
        )

        if current_symbol is not None and parent_symbol is not None:
            relationships.append(
                Relationship(
                    source=parent_symbol,
                    target=current_symbol,
                    kind=RelationshipKind.CONTAINS,
                )
            )

        if current.type in supported_call_types and parent_symbol is not None:
            callee = get_call_name(current)
            if callee is not None:
                relationships.append(
                    Relationship(
                        source=parent_symbol,
                        target=callee,
                        kind=RelationshipKind.CALLS,
                        line=current.start_point.row + 1,
                    )
                )

        next_parent = current_symbol or parent_symbol
        for child in current.children:
            visit(child, next_parent)

    for child in node.children:
        visit(child)

    return relationships
