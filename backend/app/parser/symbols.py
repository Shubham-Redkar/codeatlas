from dataclasses import dataclass
from enum import StrEnum

from tree_sitter import Node

from ..core.exceptions import UnsupportedLanguageError


class SymbolKind(StrEnum):
    """Kinds of symbols extracted from source code."""

    CLASS = "class"
    FUNCTION = "function"
    INTERFACE = "interface"


@dataclass(frozen=True, slots=True)
class Symbol:
    """A symbol extracted from a syntax tree."""

    name: str
    kind: SymbolKind
    start_byte: int
    end_byte: int
    start_line: int
    end_line: int
    parameters: tuple[str, ...] = ()
    return_type: str | None = None
    bases: tuple[str, ...] = ()
    parent_name: str | None = None


def _extract_parameters(
    node: Node,
    language: str,
) -> tuple[str, ...]:
    """Extract parameter names from a function or method node."""
    parameters_node = node.child_by_field_name("parameters")

    if parameters_node is None:
        return ()

    parameter_names: list[str] = []

    def visit(parameter: Node) -> None:
        if language == "python":
            if parameter.type in {
                "identifier",
                "typed_parameter",
                "typed_default_parameter",
                "default_parameter",
            }:
                name_node = (
                    parameter
                    if parameter.type == "identifier"
                    else parameter.child_by_field_name("name")
                )

                if name_node is None:
                    name_node = next(
                        (child for child in parameter.children if child.type == "identifier"),
                        None,
                    )

                if name_node is not None and name_node.text is not None:
                    parameter_names.append(name_node.text.decode())
                    return

        elif language == "javascript" and parameter.type in {
            "identifier",
            "assignment_pattern",
        }:
            name_node = (
                parameter
                if parameter.type == "identifier"
                else parameter.child_by_field_name("left")
            )

            if (
                name_node is not None
                and name_node.text is not None
                and name_node.type == "identifier"
            ):
                parameter_names.append(name_node.text.decode())
                return

            if name_node is not None:
                visit(name_node)
                return

        elif language == "typescript" and parameter.type in {
            "required_parameter",
            "optional_parameter",
        }:
            name_node = parameter.child_by_field_name("pattern")

            if name_node is None:
                name_node = parameter.child_by_field_name("name")

            if name_node is not None and name_node.text is not None:
                parameter_names.append(name_node.text.decode())
                return

        for child in parameter.named_children:
            visit(child)

    for child in parameters_node.named_children:
        visit(child)

    return tuple(parameter_names)


def _extract_return_type(
    node: Node,
    language: str,
) -> str | None:
    """Extract a function's declared return type, if present."""
    return_node = node.child_by_field_name("return_type")

    if return_node is None or return_node.text is None:
        return None

    return_type = return_node.text.decode()

    if language == "typescript":
        return return_type.removeprefix(":").strip()

    return return_type


def _extract_bases(
    node: Node,
    language: str,
) -> tuple[str, ...]:
    """Extract simple base-class names."""
    if language == "python":
        base_node = node.child_by_field_name("superclasses")

        if base_node is None:
            return ()

        return tuple(
            child.text.decode()
            for child in base_node.named_children
            if child.type == "identifier" and child.text is not None
        )

    if language in {"javascript", "typescript"}:
        heritage_node = next(
            (child for child in node.named_children if child.type == "class_heritage"),
            None,
        )

        if heritage_node is None:
            return ()

        bases: list[str] = []
        for child in heritage_node.named_children:
            if child.type == "extends_clause":
                bases.extend(
                    base.text.decode()
                    for base in child.named_children
                    if base.type == "identifier" and base.text is not None
                )
            elif child.type in {"identifier", "member_expression"} and child.text is not None:
                bases.append(child.text.decode())

        return tuple(bases)

    return ()


def extract_symbols(
    node: Node,
    language: str,
) -> list[Symbol]:
    """
    Extract symbols from a Tree-sitter syntax tree node.
    """
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
        "typescript": {
            "interface_declaration": SymbolKind.INTERFACE,
            "class_declaration": SymbolKind.CLASS,
            "function_declaration": SymbolKind.FUNCTION,
            "method_definition": SymbolKind.FUNCTION,
        },
    }

    symbols: list[Symbol] = []
    try:
        supported_node_types = node_types[language]
    except KeyError as exc:
        raise UnsupportedLanguageError(
            f"Unsupported language: {language}",
        ) from exc

    def visit(
        current: Node,
        parent_class: str | None = None,
    ) -> None:
        """
        Recursively extract symbols and track their containing class.
        """
        current_class = parent_class

        if language == "typescript" and current.type == "variable_declarator":
            name_node = current.child_by_field_name("name")
            value_node = current.child_by_field_name("value")

            if (
                name_node is not None
                and name_node.text is not None
                and value_node is not None
                and value_node.type == "arrow_function"
            ):
                symbols.append(
                    Symbol(
                        name=name_node.text.decode(),
                        kind=SymbolKind.FUNCTION,
                        start_byte=value_node.start_byte,
                        end_byte=value_node.end_byte,
                        start_line=value_node.start_point.row + 1,
                        end_line=value_node.end_point.row + 1,
                        parameters=_extract_parameters(value_node, language),
                        return_type=_extract_return_type(value_node, language),
                        parent_name=parent_class,
                    )
                )

        kind = supported_node_types.get(current.type)

        if kind is not None:
            name_node = current.child_by_field_name("name")

            if name_node is not None and name_node.text is not None:
                name = name_node.text.decode()
                is_function = kind == SymbolKind.FUNCTION

                symbols.append(
                    Symbol(
                        name=name,
                        kind=kind,
                        start_byte=current.start_byte,
                        end_byte=current.end_byte,
                        start_line=current.start_point.row + 1,
                        end_line=current.end_point.row + 1,
                        parameters=(
                            _extract_parameters(
                                current,
                                language,
                            )
                            if is_function
                            else ()
                        ),
                        return_type=(
                            _extract_return_type(
                                current,
                                language,
                            )
                            if is_function
                            else None
                        ),
                        bases=(
                            _extract_bases(
                                current,
                                language,
                            )
                            if kind == SymbolKind.CLASS
                            else ()
                        ),
                        parent_name=parent_class if is_function else None,
                    )
                )

                if kind == SymbolKind.CLASS:
                    current_class = name

        for child in current.children:
            visit(child, current_class)

    visit(node)
    return symbols
