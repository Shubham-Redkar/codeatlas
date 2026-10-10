from enum import StrEnum

import tree_sitter_javascript
import tree_sitter_python
import tree_sitter_typescript
from tree_sitter import Language, Parser, Tree

from ..core.exceptions import UnsupportedLanguageError


class SupportedLanguage(StrEnum):
    """Languages supported by Tree-sitter."""

    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"


def create_parser(
    language: SupportedLanguage,
) -> Parser:
    """
    Create a Tree-sitter parser for a supported language.
    """
    language_map = {
        SupportedLanguage.PYTHON: Language(tree_sitter_python.language()),
        SupportedLanguage.JAVASCRIPT: Language(tree_sitter_javascript.language()),
        SupportedLanguage.TYPESCRIPT: Language(tree_sitter_typescript.language_typescript()),
    }

    try:
        selected_language = language_map[language]
    except KeyError as exc:
        raise UnsupportedLanguageError(
            f"Unsupported language: {language}",
        ) from exc

    return Parser(selected_language)


def parse_source(
    source: bytes,
    language: SupportedLanguage,
) -> Tree:
    """
    Parse source code into a Tree-sitter syntax tree.
    """
    parser = create_parser(language)

    return parser.parse(source)
