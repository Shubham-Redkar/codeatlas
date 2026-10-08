import hashlib
from pathlib import Path

from app.ingestion.indexing import (
    FileChange,
    FileChangeType,
    build_current_file_state,
    calculate_file_hash,
    compare_files,
)


def test_calculate_file_hash(tmp_path: Path) -> None:
    file = tmp_path / "example.py"
    content = b"print('hello')\n"

    file.write_bytes(content)

    expected_hash = hashlib.sha256(content).hexdigest()

    assert calculate_file_hash(file) == expected_hash


def test_calculate_file_hash_changes_when_content_changes(
    tmp_path: Path,
) -> None:
    file = tmp_path / "example.py"

    file.write_text(
        "print('hello')\n",
        encoding="utf-8",
    )
    first_hash = calculate_file_hash(file)

    file.write_text(
        "print('goodbye')\n",
        encoding="utf-8",
    )
    second_hash = calculate_file_hash(file)

    assert first_hash != second_hash


def test_compare_files_new() -> None:
    current_files = {
        "src/main.py": "abc123",
    }
    indexed_files = {}

    changes = compare_files(
        current_files,
        indexed_files,
    )

    assert changes == [
        FileChange(
            path="src/main.py",
            change_type=FileChangeType.NEW,
        )
    ]


def test_compare_files_changed() -> None:
    current_files = {
        "src/main.py": "new-hash",
    }
    indexed_files = {
        "src/main.py": "old-hash",
    }

    changes = compare_files(
        current_files,
        indexed_files,
    )

    assert changes == [
        FileChange(
            path="src/main.py",
            change_type=FileChangeType.CHANGED,
        )
    ]


def test_compare_files_unchanged() -> None:
    current_files = {
        "src/main.py": "same-hash",
    }
    indexed_files = {
        "src/main.py": "same-hash",
    }

    changes = compare_files(
        current_files,
        indexed_files,
    )

    assert changes == [
        FileChange(
            path="src/main.py",
            change_type=FileChangeType.UNCHANGED,
        )
    ]


def test_compare_files_deleted() -> None:
    current_files = {}
    indexed_files = {
        "src/old.py": "old-hash",
    }

    changes = compare_files(
        current_files,
        indexed_files,
    )

    assert changes == [
        FileChange(
            path="src/old.py",
            change_type=FileChangeType.DELETED,
        )
    ]


def test_build_current_file_state(tmp_path: Path) -> None:
    readme = tmp_path / "README.md"
    readme.write_text(
        "# CodeAtlas\n",
        encoding="utf-8",
    )

    source_directory = tmp_path / "src"
    source_directory.mkdir()

    main = source_directory / "main.py"
    main.write_text(
        "print('hello')\n",
        encoding="utf-8",
    )

    files = [
        readme,
        main,
    ]

    state = build_current_file_state(
        repository_path=tmp_path,
        files=files,
    )

    assert set(state) == {
        "README.md",
        "src/main.py",
    }

    assert state["README.md"] == calculate_file_hash(readme)
    assert state["src/main.py"] == calculate_file_hash(main)
