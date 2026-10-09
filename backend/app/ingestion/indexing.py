import hashlib
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path


class FileChangeType(StrEnum):
    """Type of change detected for a repository file."""

    NEW = "new"
    CHANGED = "changed"
    UNCHANGED = "unchanged"
    DELETED = "deleted"


@dataclass(frozen=True, slots=True)
class FileChange:
    """Represents a detected change for a repository file."""

    path: str
    change_type: FileChangeType


def calculate_file_hash(
    path: Path,
) -> str:
    """
    Calculate the SHA-256 hash of a file.
    """
    hasher = hashlib.sha256()

    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(65536), b""):
            hasher.update(chunk)

    return hasher.hexdigest()


def compare_files(
    current_files: dict[str, str],
    indexed_files: dict[str, str],
) -> list[FileChange]:
    """
    Compare current repository files against indexed file state.
    """
    changes: list[FileChange] = []

    all_paths = sorted(set(current_files) | set(indexed_files))

    for path in all_paths:
        if path not in indexed_files:
            change_type = FileChangeType.NEW
        elif path not in current_files:
            change_type = FileChangeType.DELETED
        elif current_files[path] != indexed_files[path]:
            change_type = FileChangeType.CHANGED
        else:
            change_type = FileChangeType.UNCHANGED

        changes.append(
            FileChange(
                path=path,
                change_type=change_type,
            )
        )

    return changes


def build_current_file_state(
    repository_path: Path,
    files: list[Path],
) -> dict[str, str]:
    """
    Build repository-relative file paths and their content hashes.
    """
    return {
        path.relative_to(repository_path).as_posix(): calculate_file_hash(
            path,
        )
        for path in files
    }
