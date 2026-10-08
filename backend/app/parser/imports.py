from dataclasses import dataclass

from tree_sitter import Node


@dataclass(frozen=True, slots=True)
class Import:
    """An import extracted from a syntax tree."""

    name: str
    start_byte: int
    end_byte: int


def extract_imports(
    node: Node,
    language: str,
) -> list[Import]:
    """
    Extract imports from a Tree-sitter syntax tree node.
    """
    imports: list[Import] = []

    node_types = {
        "python": {
            "import_statement",
            "import_from_statement",
        },
        "javascript": {
            "import_statement",
        },
    }

    supported_node_types = node_types[language]

    for child in node.children:
        if child.type in supported_node_types:
            imports.append(
                Import(
                    name=child.text.decode(),
                    start_byte=child.start_byte,
                    end_byte=child.end_byte,
                )
            )

        imports.extend(extract_imports(child, language))

    return imports
