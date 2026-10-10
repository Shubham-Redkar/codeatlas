import pytest

from app.core.exceptions import UnsupportedLanguageError
from app.parser import (
    SupportedLanguage,
    SymbolKind,
    extract_ast,
    extract_symbols,
    parse_source,
)


def test_extract_symbols_rejects_unsupported_language() -> None:
    tree = parse_source(
        b"def hello():\n    pass\n",
        SupportedLanguage.PYTHON,
    )
    ast = extract_ast(tree)

    with pytest.raises(UnsupportedLanguageError, match="Unsupported language"):
        extract_symbols(ast, "ruby")


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
        "getName",
        "createUser",
    ]

    assert [symbol.kind for symbol in symbols] == [
        SymbolKind.CLASS,
        SymbolKind.FUNCTION,
        SymbolKind.FUNCTION,
    ]


def test_extract_python_symbol_line_ranges() -> None:
    source = b"class User:\n    def get_name(self):\n        return 'name'\n"

    tree = parse_source(source, SupportedLanguage.PYTHON)
    ast = extract_ast(tree)

    symbols = extract_symbols(ast, SupportedLanguage.PYTHON)

    assert [(symbol.name, symbol.start_line, symbol.end_line) for symbol in symbols] == [
        ("User", 1, 3),
        ("get_name", 2, 3),
    ]


def test_extract_javascript_symbol_line_ranges() -> None:
    source = b'class User {\n    getName() {\n        return "name";\n    }\n}\n'

    tree = parse_source(source, SupportedLanguage.JAVASCRIPT)
    ast = extract_ast(tree)

    symbols = extract_symbols(ast, SupportedLanguage.JAVASCRIPT)

    assert [(symbol.name, symbol.start_line, symbol.end_line) for symbol in symbols] == [
        ("User", 1, 5),
        ("getName", 2, 4),
    ]


def test_extract_python_function_metadata() -> None:
    source = b"def greet(name: str, age: int = 18) -> str:\n    return name\n"

    tree = parse_source(source, SupportedLanguage.PYTHON)
    ast = extract_ast(tree)

    symbols = extract_symbols(ast, SupportedLanguage.PYTHON)

    greet = next(symbol for symbol in symbols if symbol.name == "greet")

    assert greet.parameters == ("name", "age")
    assert greet.return_type == "str"


def test_extract_javascript_function_metadata() -> None:
    source = b"function greet(name, age = 18) {\n    return name;\n}\n"

    tree = parse_source(source, SupportedLanguage.JAVASCRIPT)
    ast = extract_ast(tree)

    symbols = extract_symbols(ast, SupportedLanguage.JAVASCRIPT)

    greet = next(symbol for symbol in symbols if symbol.name == "greet")

    assert greet.parameters == ("name", "age")
    assert greet.return_type is None


def test_extract_python_class_inheritance() -> None:
    source = b"class Admin(User, Auditable):\n    pass\n"

    tree = parse_source(source, SupportedLanguage.PYTHON)
    ast = extract_ast(tree)

    symbols = extract_symbols(ast, SupportedLanguage.PYTHON)
    admin = next(symbol for symbol in symbols if symbol.name == "Admin")

    assert admin.bases == ("User", "Auditable")


def test_extract_javascript_class_inheritance() -> None:
    source = b"class Admin extends User {\n    run() {}\n}\n"

    tree = parse_source(source, SupportedLanguage.JAVASCRIPT)
    ast = extract_ast(tree)

    symbols = extract_symbols(ast, SupportedLanguage.JAVASCRIPT)
    admin = next(symbol for symbol in symbols if symbol.name == "Admin")

    assert admin.bases == ("User",)


def test_extract_python_method_parent() -> None:
    source = b"class User:\n    def get_name(self):\n        return 'name'\n"

    tree = parse_source(source, SupportedLanguage.PYTHON)
    ast = extract_ast(tree)

    symbols = extract_symbols(ast, SupportedLanguage.PYTHON)
    method = next(symbol for symbol in symbols if symbol.name == "get_name")

    assert method.parent_name == "User"


def test_extract_python_symbols_with_malformed_syntax() -> None:
    source = b"""
def broken(
    pass

def valid_function():
    return 42
"""

    tree = parse_source(source, SupportedLanguage.PYTHON)
    ast = extract_ast(tree)

    symbols = extract_symbols(ast, SupportedLanguage.PYTHON)

    assert tree.root_node.has_error is True
    assert isinstance(symbols, list)


def test_extract_typescript_symbols() -> None:
    source = b"""
interface User {
    id: number;
}

class UserService extends BaseService {
    getUser(id: number): User {
        return createUser(id);
    }
}

function createUser(id: number): User {
    return { id };
}
"""

    tree = parse_source(source, SupportedLanguage.TYPESCRIPT)
    ast = extract_ast(tree)

    symbols = extract_symbols(ast, SupportedLanguage.TYPESCRIPT)

    assert [(symbol.name, symbol.kind) for symbol in symbols] == [
        ("User", SymbolKind.INTERFACE),
        ("UserService", SymbolKind.CLASS),
        ("getUser", SymbolKind.FUNCTION),
        ("createUser", SymbolKind.FUNCTION),
    ]
    assert symbols[1].bases == ("BaseService",)
    assert symbols[2].parent_name == "UserService"
    assert symbols[2].parameters == ("id",)
    assert symbols[3].parameters == ("id",)


def test_extract_typescript_function_metadata() -> None:
    source = b"""
function createUser(id: number): User {
    return { id };
}

class UserService {
    getUser(id: number): User {
        return createUser(id);
    }
}
"""

    tree = parse_source(source, SupportedLanguage.TYPESCRIPT)
    ast = extract_ast(tree)

    symbols = extract_symbols(ast, SupportedLanguage.TYPESCRIPT)

    create_user = next(symbol for symbol in symbols if symbol.name == "createUser")
    get_user = next(symbol for symbol in symbols if symbol.name == "getUser")

    assert create_user.parameters == ("id",)
    assert create_user.return_type == "User"
    assert get_user.parameters == ("id",)
    assert get_user.return_type == "User"


def test_extract_typescript_arrow_function() -> None:
    source = b"""
const findUser = (id: number): User => createUser(id);
"""

    tree = parse_source(source, SupportedLanguage.TYPESCRIPT)
    ast = extract_ast(tree)

    symbols = extract_symbols(ast, SupportedLanguage.TYPESCRIPT)

    assert len(symbols) == 1
    assert symbols[0].name == "findUser"
    assert symbols[0].kind == SymbolKind.FUNCTION
    assert symbols[0].parameters == ("id",)
    assert symbols[0].return_type == "User"
