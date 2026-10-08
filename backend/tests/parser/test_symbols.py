from app.parser import (
    SupportedLanguage,
    SymbolKind,
    extract_ast,
    extract_symbols,
    parse_source,
)


def test_extract_python_symbols() -> None:
    source = b"""
class User:
    def get_name(self):
        return "name"

def create_user():
    return User()
"""

    tree = parse_source(source, SupportedLanguage.PYTHON)
    ast = extract_ast(tree)

    symbols = extract_symbols(ast, SupportedLanguage.PYTHON)

    assert [(symbol.name, symbol.kind) for symbol in symbols] == [
        ("User", SymbolKind.CLASS),
        ("get_name", SymbolKind.FUNCTION),
        ("create_user", SymbolKind.FUNCTION),
    ]


def test_extract_javascript_symbols() -> None:
    source = b"""
class User {
    getName() {
        return "name";
    }
}

function createUser() {
    return new User();
}
"""

    tree = parse_source(source, SupportedLanguage.JAVASCRIPT)
    ast = extract_ast(tree)

    symbols = extract_symbols(ast, SupportedLanguage.JAVASCRIPT)

    assert [symbol.name for symbol in symbols] == [
        "User",
        "createUser",
    ]

    assert [symbol.kind for symbol in symbols] == [
        SymbolKind.CLASS,
        SymbolKind.FUNCTION,
    ]
