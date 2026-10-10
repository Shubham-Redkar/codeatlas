from dataclasses import dataclass

from tree_sitter import Node

from ..core.exceptions import UnsupportedLanguageError


@dataclass(frozen=True, slots=True)
class Import:
    """An import extracted from a syntax tree."""

    name: str
    start_byte: int
    end_byte: int
    module: str
    imported_names: tuple[str, ...] = ()
    aliases: tuple[tuple[str, str], ...] = ()


def _text(node: Node | None) -> str | None:
    """
    Decode a syntax node's source text, returning None when unavailable.
    """
    if node is None or node.text is None:
        return None
    return node.text.decode()


def _python_import_metadata(
    node: Node,
) -> tuple[str, tuple[str, ...], tuple[tuple[str, str], ...]]:
    """
    Extract the module, imported names, and aliases from a Python import.
    """
    module = ""
    imported_names: list[str] = []
    aliases: list[tuple[str, str]] = []

    if node.type == "import_statement":
        for child in node.named_children:
            if child.type == "dotted_name":
                imported = _text(child)
                if imported is not None:
                    imported_names.append(imported)
                    aliases.append((imported, imported))
            elif child.type == "aliased_import":
                name_node = child.child_by_field_name("name")
                alias_node = child.child_by_field_name("alias")
                imported = _text(name_node)
                alias = _text(alias_node)
                if imported is not None:
                    imported_names.append(imported)
                    aliases.append((imported, alias or imported))

    elif node.type == "import_from_statement":
        module_node = node.child_by_field_name("module_name")
        module = _text(module_node) or ""

        for child in node.named_children:
            if child == module_node:
                continue

            if child.type == "dotted_name":
                imported = _text(child)
                if imported is not None:
                    imported_names.append(imported)
                    aliases.append((imported, imported))
            elif child.type == "aliased_import":
                name_node = child.child_by_field_name("name")
                alias_node = child.child_by_field_name("alias")
                imported = _text(name_node)
                alias = _text(alias_node)
                if imported is not None:
                    imported_names.append(imported)
                    aliases.append((imported, alias or imported))

    return module, tuple(imported_names), tuple(aliases)


def _javascript_import_metadata(
    node: Node,
) -> tuple[str, tuple[str, ...], tuple[tuple[str, str], ...]]:
    """
    Extract the source module, imported names, and aliases from a JS import.
    """
    module = ""
    imported_names: list[str] = []
    aliases: list[tuple[str, str]] = []

    for child in node.named_children:
        if child.type == "string":
            module_text = _text(child)
            if module_text is not None:
                module = module_text.strip("'\"")
        elif child.type == "import_clause":
            for item in child.named_children:
                if item.type == "identifier":
                    imported = _text(item)
                    if imported is not None:
                        imported_names.append("default")
                        aliases.append(("default", imported))
                elif item.type == "named_imports":
                    for specifier in item.named_children:
                        if specifier.type != "import_specifier":
                            continue
                        imported = _text(specifier.child_by_field_name("name"))
                        alias = _text(specifier.child_by_field_name("alias"))
                        if imported is not None:
                            imported_names.append(imported)
                            aliases.append((imported, alias or imported))
                elif item.type == "namespace_import":
                    alias_node = next(
                        (child for child in item.named_children if child.type == "identifier"),
                        None,
                    )
                    alias = _text(alias_node)
                    if alias is not None:
                        imported_names.append("*")
                        aliases.append(("*", alias))

    return module, tuple(imported_names), tuple(aliases)


def extract_imports(
    node: Node,
    language: str,
) -> list[Import]:
    """
    Extract imports from a Tree-sitter syntax tree node.
    """
    node_types = {
        "python": {
            "import_statement",
            "import_from_statement",
        },
        "javascript": {
            "import_statement",
        },
        "typescript": {
            "import_statement",
        },
    }

    imports: list[Import] = []

    try:
        supported_node_types = node_types[language]
    except KeyError as exc:
        raise UnsupportedLanguageError(f"Unsupported language: {language}") from exc

    def visit(current: Node) -> None:
        """Collect an import from the current node, then visit its children."""
        if current.type in supported_node_types and current.text is not None:
            if language == "python":
                module, imported_names, aliases = _python_import_metadata(current)
            elif language in {"javascript", "typescript"}:
                module, imported_names, aliases = _javascript_import_metadata(current)
            else:
                raise UnsupportedLanguageError(f"Unsupported language: {language}")

            imports.append(
                Import(
                    name=current.text.decode(),
                    start_byte=current.start_byte,
                    end_byte=current.end_byte,
                    module=module,
                    imported_names=imported_names,
                    aliases=aliases,
                )
            )

        for child in current.children:
            visit(child)

    visit(node)
    return imports
