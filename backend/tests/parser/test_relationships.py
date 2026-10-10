import pytest

from app.core.exceptions import UnsupportedLanguageError
from app.parser import (
    Relationship,
    RelationshipKind,
    SupportedLanguage,
    extract_ast,
    extract_relationships,
    parse_source,
)


def test_extract_relationships_rejects_unsupported_language() -> None:
    source = b"def helper(): pass"

    tree = parse_source(source, SupportedLanguage.PYTHON)
    ast = extract_ast(tree)

    with pytest.raises(UnsupportedLanguageError, match="Unsupported language"):
        extract_relationships(ast, "ruby")


def test_extract_python_relationships() -> None:
    source = b"""
class User:
    def get_name(self):
        return "name"

def create_user():
    return User()
"""

    tree = parse_source(source, SupportedLanguage.PYTHON)
    ast = extract_ast(tree)

    relationships = extract_relationships(
        ast,
        SupportedLanguage.PYTHON,
    )

    assert [
        relationship
        for relationship in relationships
        if relationship.kind == RelationshipKind.CONTAINS
    ] == [
        Relationship(
            source="User",
            target="get_name",
            kind=RelationshipKind.CONTAINS,
        ),
    ]


def test_extract_javascript_relationships() -> None:
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

    relationships = extract_relationships(
        ast,
        SupportedLanguage.JAVASCRIPT,
    )

    assert relationships == [
        Relationship(
            source="User",
            target="getName",
            kind=RelationshipKind.CONTAINS,
        ),
    ]


def test_extract_python_call_relationships() -> None:
    source = b"""
def create_user():
    user = User()
    return save_user(user)
"""

    tree = parse_source(source, SupportedLanguage.PYTHON)
    ast = extract_ast(tree)

    relationships = extract_relationships(ast, SupportedLanguage.PYTHON)

    calls = [
        relationship
        for relationship in relationships
        if relationship.kind == RelationshipKind.CALLS
    ]

    assert [(call.source, call.target, call.line) for call in calls] == [
        ("create_user", "User", 3),
        ("create_user", "save_user", 4),
    ]


def test_extract_javascript_call_relationships() -> None:
    source = b"""
function createUser() {
    return saveUser();
}
"""

    tree = parse_source(source, SupportedLanguage.JAVASCRIPT)
    ast = extract_ast(tree)

    relationships = extract_relationships(
        ast,
        SupportedLanguage.JAVASCRIPT,
    )

    calls = [
        relationship
        for relationship in relationships
        if relationship.kind == RelationshipKind.CALLS
    ]

    assert [(call.source, call.target, call.line) for call in calls] == [
        ("createUser", "saveUser", 3)
    ]


def test_extract_python_method_calls() -> None:
    source = b"""
class UserService:
    def create(self):
        self.validate()
        repository.save()
"""

    tree = parse_source(source, SupportedLanguage.PYTHON)
    ast = extract_ast(tree)

    relationships = extract_relationships(ast, SupportedLanguage.PYTHON)

    calls = [
        relationship
        for relationship in relationships
        if relationship.kind == RelationshipKind.CALLS
    ]

    assert [(call.source, call.target, call.line) for call in calls] == [
        ("create", "self.validate", 4),
        ("create", "repository.save", 5),
    ]


def test_extract_nested_python_function_calls() -> None:
    source = b"""
def outer():
    def inner():
        helper()
    inner()
"""

    tree = parse_source(source, SupportedLanguage.PYTHON)
    ast = extract_ast(tree)

    relationships = extract_relationships(ast, SupportedLanguage.PYTHON)

    calls = [
        relationship
        for relationship in relationships
        if relationship.kind == RelationshipKind.CALLS
    ]

    assert [(call.source, call.target, call.line) for call in calls] == [
        ("inner", "helper", 4),
        ("outer", "inner", 5),
    ]


def test_extract_javascript_method_calls() -> None:
    source = b"""
class UserService {
    create() {
        this.validate();
        repository.save();
    }
}
"""

    tree = parse_source(source, SupportedLanguage.JAVASCRIPT)
    ast = extract_ast(tree)

    relationships = extract_relationships(
        ast,
        SupportedLanguage.JAVASCRIPT,
    )

    calls = [
        relationship
        for relationship in relationships
        if relationship.kind == RelationshipKind.CALLS
    ]

    assert [(call.source, call.target, call.line) for call in calls] == [
        ("create", "this.validate", 4),
        ("create", "repository.save", 5),
    ]


def test_extract_nested_javascript_function_calls() -> None:
    source = b"""
function outer() {
    function inner() {
        helper();
    }
    inner();
}
"""

    tree = parse_source(source, SupportedLanguage.JAVASCRIPT)
    ast = extract_ast(tree)

    relationships = extract_relationships(
        ast,
        SupportedLanguage.JAVASCRIPT,
    )

    calls = [
        relationship
        for relationship in relationships
        if relationship.kind == RelationshipKind.CALLS
    ]

    assert [(call.source, call.target, call.line) for call in calls] == [
        ("inner", "helper", 4),
        ("outer", "inner", 6),
    ]


def test_extract_relationships_with_malformed_python_syntax() -> None:
    source = b"""
def broken():
    helper(
"""

    tree = parse_source(source, SupportedLanguage.PYTHON)

    assert tree.root_node.has_error

    ast = extract_ast(tree)
    relationships = extract_relationships(
        ast,
        SupportedLanguage.PYTHON,
    )

    assert isinstance(relationships, list)


def test_extract_typescript_relationships() -> None:
    source = b"""
class UserService {
    getUser(id: number): User {
        return findUser(id);
    }
}

function findUser(id: number): User {
    return loadUser(id);
}
"""

    tree = parse_source(source, SupportedLanguage.TYPESCRIPT)
    ast = extract_ast(tree)

    relationships = extract_relationships(ast, SupportedLanguage.TYPESCRIPT)

    assert [
        (relationship.source, relationship.target, relationship.kind)
        for relationship in relationships
        if relationship.kind == RelationshipKind.CONTAINS
    ] == [
        ("UserService", "getUser", RelationshipKind.CONTAINS),
    ]

    calls = [
        (relationship.source, relationship.target, relationship.line)
        for relationship in relationships
        if relationship.kind == RelationshipKind.CALLS
    ]

    assert calls == [
        ("getUser", "findUser", 4),
        ("findUser", "loadUser", 9),
    ]
