from enum import StrEnum

import tree_sitter_javascript
import tree_sitter_python
from tree_sitter import Language, Parser, Tree


class SupportedLanguage(StrEnum):
    """Languages supported by Tree-sitter."""

    PYTHON = "python"
    JAVASCRIPT = "javascript"


def create_parser(
    language: SupportedLanguage,
) -> Parser:
    """
    Create a Tree-sitter parser for a supported language.
    """
    language_map = {
        SupportedLanguage.PYTHON: Language(tree_sitter_python.language()),
        SupportedLanguage.JAVASCRIPT: Language(tree_sitter_javascript.language()),
    }

    return Parser(language_map[language])


def parse_source(
    source: bytes,
    language: SupportedLanguage,
) -> Tree:
    """
    Parse source code into a Tree-sitter syntax tree.
    """
    parser = create_parser(language)

    return parser.parse(source)
