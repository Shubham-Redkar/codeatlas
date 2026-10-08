import pytest
from tree_sitter import Parser, Tree

from app.parser import (
    SupportedLanguage,
    create_parser,
    parse_source,
)


@pytest.mark.parametrize(
    "language",
    [
        SupportedLanguage.PYTHON,
        SupportedLanguage.JAVASCRIPT,
    ],
)
def test_create_parser(language: SupportedLanguage) -> None:
    parser = create_parser(language)

    assert isinstance(parser, Parser)


@pytest.mark.parametrize(
    ("language", "source"),
    [
        (
            SupportedLanguage.PYTHON,
            b"def hello():\n    return 'hello'\n",
        ),
        (
            SupportedLanguage.JAVASCRIPT,
            b"function hello() {\n    return 'hello';\n}\n",
        ),
    ],
)
def test_parse_source(
    language: SupportedLanguage,
    source: bytes,
) -> None:
    tree = parse_source(source, language)

    assert isinstance(tree, Tree)
    assert tree.root_node.has_error is False


def test_parse_source_with_syntax_error() -> None:
    tree = parse_source(
        b"def hello(:\n    return 'hello'\n",
        SupportedLanguage.PYTHON,
    )

    assert isinstance(tree, Tree)
    assert tree.root_node.has_error is True
