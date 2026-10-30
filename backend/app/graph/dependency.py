from dataclasses import dataclass
from pathlib import PurePosixPath

from ..parser import Import


@dataclass(frozen=True, slots=True)
class Dependency:
    """A dependency between two repository files."""

    source: str
    target: str


@dataclass(frozen=True, slots=True)
class DependencyGraph:
    """An in-memory dependency graph."""

    dependencies: tuple[Dependency, ...]

    @property
    def nodes(self) -> frozenset[str]:
        """Return all files participating in the graph."""
        return frozenset(
            {dependency.source for dependency in self.dependencies}
            | {dependency.target for dependency in self.dependencies}
        )

    def get_dependencies(
        self,
        source: str,
    ) -> frozenset[str]:
        """Return the files directly depended on by a source file."""
        return frozenset(
            dependency.target for dependency in self.dependencies if dependency.source == source
        )

    def get_dependents(self, target: str) -> frozenset[str]:
        """Return files that directly depend on a target file."""
        return frozenset(
            dependency.source for dependency in self.dependencies if dependency.target == target
        )

    def get_transitive_dependencies(
        self,
        source: str,
    ) -> frozenset[str]:
        """Return all transitively reachable dependencies, excluding source."""
        visited: set[str] = set()
        pending = list(self.get_dependencies(source))

        while pending:
            current = pending.pop()

            if current == source or current in visited:
                continue

            visited.add(current)
            pending.extend(self.get_dependencies(current) - visited)

        return frozenset(visited)

    def get_transitive_dependents(
        self,
        target: str,
    ) -> frozenset[str]:
        """Return all transitively dependent files, excluding target."""
        visited: set[str] = set()
        pending = list(self.get_dependents(target))

        while pending:
            current = pending.pop()

            if current == target or current in visited:
                continue

            visited.add(current)
            pending.extend(self.get_dependents(current) - visited)

        return frozenset(visited)


def build_dependency_graph(
    dependencies: list[Dependency],
) -> DependencyGraph:
    """
    Build a dependency graph from file dependencies.
    """
    return DependencyGraph(
        dependencies=tuple(dependencies),
    )


def resolve_python_import(
    import_statement: Import,
    available_files: set[str],
    source: str | None = None,
) -> str | None:
    """
    Resolve a Python import statement to a repository file.
    """
    module = import_statement.module

    if module.startswith("."):
        if source is None:
            return None

        source_path = PurePosixPath(source)

        package_path = source_path.parent
        if source_path.name == "__init__.py":
            package_path = source_path.parent

        level = len(module) - len(module.lstrip("."))
        for _ in range(level - 1):
            package_path = package_path.parent

        relative_module = module[level:]
        if relative_module:
            package_path = package_path / PurePosixPath(*relative_module.split("."))

        candidates: list[str] = []

        if relative_module:
            candidates.extend(
                [
                    f"{package_path}.py",
                    str(package_path / "__init__.py"),
                ]
            )

        for imported_name in import_statement.imported_names:
            if imported_name == "*":
                continue

            imported_path = package_path / imported_name
            candidates.extend(
                [
                    f"{imported_path}.py",
                    str(imported_path / "__init__.py"),
                ]
            )

        return next(
            (candidate for candidate in candidates if candidate in available_files),
            None,
        )

    if not module:
        return None

    module_path = PurePosixPath(*module.split("."))
    candidates: list[str] = [
        f"{module_path}.py",
        str(module_path / "__init__.py"),
    ]

    return next(
        (candidate for candidate in candidates if candidate in available_files),
        None,
    )


def _resolve_python_imports(
    import_statement: Import,
    available_files: set[str],
    source: str,
) -> list[str]:
    """Resolve a Python import to all matching repository files."""
    module = import_statement.module

    if not module:
        target = resolve_python_import(
            import_statement,
            available_files,
            source=source,
        )
        return [target] if target is not None else []

    if module.startswith("."):
        source_path = PurePosixPath(source)
        package_path = source_path.parent

        level = len(module) - len(module.lstrip("."))
        for _ in range(level - 1):
            package_path = package_path.parent

        relative_module = module[level:]
        if relative_module:
            package_path = package_path / PurePosixPath(*relative_module.split("."))

        targets = [
            str(candidate)
            for imported_name in import_statement.imported_names
            if imported_name != "*"
            for candidate in (
                package_path / f"{imported_name}.py",
                package_path / imported_name / "__init__.py",
            )
            if str(candidate) in available_files
        ]

        if targets:
            return targets

    else:
        module_path = PurePosixPath(*module.split("."))

        targets = [
            str(candidate)
            for imported_name in import_statement.imported_names
            if imported_name != "*"
            for candidate in (
                module_path / f"{imported_name}.py",
                module_path / imported_name / "__init__.py",
            )
            if str(candidate) in available_files
        ]

        if targets:
            return targets

    target = resolve_python_import(
        import_statement,
        available_files,
        source=source,
    )
    return [target] if target is not None else []


def build_python_dependencies(
    source: str,
    imports: list[Import],
    available_files: set[str],
) -> list[Dependency]:
    """
    Build repository dependencies from Python imports.
    """
    dependencies: list[Dependency] = []

    for import_statement in imports:
        targets = _resolve_python_imports(
            import_statement,
            available_files,
            source,
        )

        dependencies.extend(
            Dependency(
                source=source,
                target=target,
            )
            for target in targets
        )

    return dependencies


def build_python_dependency_graph(
    imports_by_file: dict[str, list[Import]],
    available_files: set[str],
) -> DependencyGraph:
    """Build a dependency graph from imports across Python repository files."""
    dependencies: list[Dependency] = []

    for source, imports in imports_by_file.items():
        dependencies.extend(
            build_python_dependencies(
                source=source,
                imports=imports,
                available_files=available_files,
            )
        )

    return build_dependency_graph(dependencies)
