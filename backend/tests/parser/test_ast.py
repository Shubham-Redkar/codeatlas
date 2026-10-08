from tree_sitter import Node

from app.parser import (
    SupportedLanguage,
    extract_ast,
    parse_source,
)


def test_extract_ast() -> None:
    tree = parse_source(
        b"def hello():\n    return 'hello'\n",
        SupportedLanguage.PYTHON,
    )

    ast = extract_ast(tree)

    assert isinstance(ast, Node)
    assert ast.type == "module"
    assert ast.has_error is False
