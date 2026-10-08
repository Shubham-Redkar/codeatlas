from dataclasses import dataclass
from enum import StrEnum

from tree_sitter import Node


class SymbolKind(StrEnum):
    """Kinds of symbols extracted from source code."""

    CLASS = "class"
    FUNCTION = "function"


@dataclass(frozen=True, slots=True)
class Symbol:
    """A symbol extracted from a syntax tree."""

    name: str
    kind: SymbolKind
    start_byte: int
    end_byte: int


def extract_symbols(
    node: Node,
    language: str,
) -> list[Symbol]:
    """
    Extract symbols from a Tree-sitter syntax tree node.
    """
    symbols: list[Symbol] = []

    node_types = {
        "python": {
            "class_definition": SymbolKind.CLASS,
            "function_definition": SymbolKind.FUNCTION,
        },
        "javascript": {
            "class_declaration": SymbolKind.CLASS,
            "function_declaration": SymbolKind.FUNCTION,
            "method_definition": SymbolKind.FUNCTION,
        },
    }

    supported_node_types = node_types[language]

    for child in node.children:
        if child.type in supported_node_types:
            name_node = child.child_by_field_name("name")

            if name_node is not None:
                symbols.append(
                    Symbol(
                        name=name_node.text.decode(),
                        kind=supported_node_types[child.type],
                        start_byte=child.start_byte,
                        end_byte=child.end_byte,
                    )
                )

        symbols.extend(extract_symbols(child, language))

    return symbols
