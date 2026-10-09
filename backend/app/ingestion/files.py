from pathlib import Path

from ..core.exceptions import RepositoryPathError


def discover_files(
    repository_path: Path,
) -> list[Path]:
    """
    Discover all files inside a repository recursively.
    """
    if not repository_path.is_dir():
        raise RepositoryPathError(
            f"Repository directory not found: {repository_path}",
        )

    return [path for path in repository_path.rglob("*") if path.is_file()]
