from app.parser import (
    Relationship,
    RelationshipKind,
    SupportedLanguage,
    extract_ast,
    extract_relationships,
    parse_source,
)


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

    assert relationships == [
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
