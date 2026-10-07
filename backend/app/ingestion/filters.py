from pathlib import Path

IGNORED_DIRECTORIES: frozenset[str] = frozenset(
    {
        ".git",
        "node_modules",
        ".venv",
        "venv",
        "env",
        "__pycache__",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
        "dist",
        "build",
        "coverage",
    }
)

IGNORED_SUFFIXES: frozenset[str] = frozenset(
    {
        ".pyc",
        ".pyo",
        ".o",
        ".so",
        ".class",
    }
)


def filter_files(
    files: list[Path],
) -> list[Path]:
    """
    Filter out files that should not be analyzed by CodeAtlas.
    """
    return [
        path
        for path in files
        if not any(directory in IGNORED_DIRECTORIES for directory in path.parts)
        and path.suffix.lower() not in IGNORED_SUFFIXES
    ]
