from pathlib import Path


def discover_files(
    repository_path: Path,
) -> list[Path]:
    """
    Discover all files inside a repository recursively.
    """
    return [path for path in repository_path.rglob("*") if path.is_file()]
