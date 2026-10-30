from app.graph import (
    Dependency,
    DependencyGraph,
    build_dependency_graph,
    build_python_dependencies,
    build_python_dependency_graph,
    resolve_python_import,
)
from app.parser import Import


def test_build_dependency_graph() -> None:
    dependencies = [
        Dependency(
            source="app/services/indexing.py",
            target="app/ingestion/files.py",
        ),
        Dependency(
            source="app/services/indexing.py",
            target="app/database/repositories/repository_file.py",
        ),
    ]

    graph = build_dependency_graph(dependencies)

    assert isinstance(graph, DependencyGraph)
    assert graph.dependencies == tuple(dependencies)
    assert graph.nodes == frozenset(
        {
            "app/services/indexing.py",
            "app/ingestion/files.py",
            "app/database/repositories/repository_file.py",
        }
    )


def test_resolve_python_import() -> None:
    available_files = {
        "app/services/indexing.py",
        "app/parser/__init__.py",
        "app/parser/ast.py",
        "tests/test_indexing.py",
    }

    assert (
        resolve_python_import(
            Import(
                name="import app.services.indexing",
                start_byte=0,
                end_byte=29,
                module="app.services.indexing",
            ),
            available_files,
        )
        == "app/services/indexing.py"
    )

    assert (
        resolve_python_import(
            Import(
                name="from app.parser import parse_source",
                start_byte=0,
                end_byte=35,
                module="app.parser",
                imported_names=("parse_source",),
            ),
            available_files,
        )
        == "app/parser/__init__.py"
    )

    assert (
        resolve_python_import(
            Import(
                name="from pathlib import Path",
                start_byte=0,
                end_byte=25,
                module="pathlib",
                imported_names=("Path",),
            ),
            available_files,
        )
        is None
    )


def test_build_python_dependencies() -> None:
    imports = [
        Import(
            name="import app.services.indexing",
            start_byte=0,
            end_byte=29,
            module="app.services.indexing",
        ),
        Import(
            name="from pathlib import Path",
            start_byte=30,
            end_byte=55,
            module="pathlib",
            imported_names=("Path",),
        ),
    ]

    available_files = {
        "app/services/indexing.py",
    }

    dependencies = build_python_dependencies(
        source="app/main.py",
        imports=imports,
        available_files=available_files,
    )

    assert dependencies == [
        Dependency(
            source="app/main.py",
            target="app/services/indexing.py",
        ),
    ]


def test_resolve_relative_python_import() -> None:
    available_files = {
        "app/services/__init__.py",
        "app/services/helpers.py",
        "app/services/indexing.py",
    }

    result = resolve_python_import(
        Import(
            name="from . import helpers",
            start_byte=0,
            end_byte=22,
            module=".",
            imported_names=("helpers",),
        ),
        available_files,
        source="app/services/indexing.py",
    )

    assert result == "app/services/helpers.py"


def test_get_direct_dependencies() -> None:
    graph = build_dependency_graph(
        [
            Dependency(source="main.py", target="services.py"),
            Dependency(source="main.py", target="config.py"),
            Dependency(source="services.py", target="database.py"),
        ]
    )

    assert graph.get_dependencies("main.py") == frozenset({"services.py", "config.py"})


def test_get_transitive_dependencies() -> None:
    graph = build_dependency_graph(
        [
            Dependency(source="main.py", target="services.py"),
            Dependency(source="services.py", target="database.py"),
        ]
    )

    assert graph.get_transitive_dependencies("main.py") == frozenset({"services.py", "database.py"})


def test_get_transitive_dependents() -> None:
    graph = build_dependency_graph(
        [
            Dependency(source="main.py", target="services.py"),
            Dependency(source="services.py", target="database.py"),
        ]
    )

    assert graph.get_transitive_dependents("database.py") == frozenset({"services.py", "main.py"})


def test_transitive_dependencies_handles_cycles() -> None:
    graph = build_dependency_graph(
        [
            Dependency(source="a.py", target="b.py"),
            Dependency(source="b.py", target="c.py"),
            Dependency(source="c.py", target="a.py"),
        ]
    )

    assert graph.get_transitive_dependencies("a.py") == frozenset({"b.py", "c.py"})


def test_resolve_relative_import_from_package_initializer() -> None:
    """Resolve a relative import originating from a package initializer."""
    available_files = {
        "app/__init__.py",
        "app/services/__init__.py",
        "app/services/helpers.py",
    }

    result = resolve_python_import(
        Import(
            name="from .services import helpers",
            start_byte=0,
            end_byte=29,
            module=".services",
            imported_names=("helpers",),
        ),
        available_files,
        source="app/__init__.py",
    )

    assert result == "app/services/__init__.py"

    submodule_result = resolve_python_import(
        Import(
            name="from .services.helpers import helper",
            start_byte=0,
            end_byte=43,
            module=".services.helpers",
            imported_names=("helper",),
        ),
        available_files,
        source="app/__init__.py",
    )

    assert submodule_result == "app/services/helpers.py"


def test_build_python_dependency_graph() -> None:
    """Build a graph from imports across multiple Python files."""
    imports_by_file = {
        "app/main.py": [
            Import(
                name="from app.services import indexing",
                start_byte=0,
                end_byte=36,
                module="app.services",
                imported_names=("indexing",),
            ),
        ],
        "app/services/indexing.py": [
            Import(
                name="from app.database import repository",
                start_byte=0,
                end_byte=38,
                module="app.database",
                imported_names=("repository",),
            ),
        ],
    }
    available_files = {
        "app/main.py",
        "app/services/__init__.py",
        "app/services/indexing.py",
        "app/database/__init__.py",
    }

    graph = build_python_dependency_graph(
        imports_by_file=imports_by_file,
        available_files=available_files,
    )

    assert graph.get_dependencies("app/main.py") == frozenset({"app/services/indexing.py"})
    assert graph.get_dependencies("app/services/indexing.py") == frozenset(
        {"app/database/__init__.py"}
    )


def test_build_python_dependencies_resolves_multiple_imported_names() -> None:
    """Resolve multiple imported submodules into separate dependencies."""
    imports = [
        Import(
            name="from app.services import indexing, helpers",
            start_byte=0,
            end_byte=47,
            module="app.services",
            imported_names=("indexing", "helpers"),
            aliases=(("indexing", "indexing"), ("helpers", "helpers")),
        ),
    ]
    available_files = {
        "app/services/__init__.py",
        "app/services/indexing.py",
        "app/services/helpers.py",
    }

    dependencies = build_python_dependencies(
        source="app/main.py",
        imports=imports,
        available_files=available_files,
    )

    assert dependencies == [
        Dependency(
            source="app/main.py",
            target="app/services/indexing.py",
        ),
        Dependency(
            source="app/main.py",
            target="app/services/helpers.py",
        ),
    ]


def test_build_python_dependencies_resolves_multiple_relative_submodules() -> None:
    """Resolve multiple submodules imported through a relative import."""
    imports = [
        Import(
            name="from . import helpers, indexing",
            start_byte=0,
            end_byte=32,
            module=".",
            imported_names=("helpers", "indexing"),
            aliases=(("helpers", "helpers"), ("indexing", "indexing")),
        ),
    ]
    available_files = {
        "app/services/__init__.py",
        "app/services/helpers.py",
        "app/services/indexing.py",
    }

    dependencies = build_python_dependencies(
        source="app/services/consumer.py",
        imports=imports,
        available_files=available_files,
    )

    assert dependencies == [
        Dependency(
            source="app/services/consumer.py",
            target="app/services/helpers.py",
        ),
        Dependency(
            source="app/services/consumer.py",
            target="app/services/indexing.py",
        ),
    ]


def test_build_python_dependencies_falls_back_to_package_for_symbols() -> None:
    """Use the package initializer when an imported name is not a submodule."""
    imports = [
        Import(
            name="from app.parser import parse_source",
            start_byte=0,
            end_byte=35,
            module="app.parser",
            imported_names=("parse_source",),
        ),
    ]
    available_files = {
        "app/parser/__init__.py",
        "app/parser/tree_sitter.py",
    }

    dependencies = build_python_dependencies(
        source="app/main.py",
        imports=imports,
        available_files=available_files,
    )

    assert dependencies == [
        Dependency(
            source="app/main.py",
            target="app/parser/__init__.py",
        ),
    ]
