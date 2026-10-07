from pathlib import Path

from app.ingestion.filters import filter_files


def test_filter_files() -> None:
    files = [
        Path("repo/README.md"),
        Path("repo/src/main.py"),
        Path("repo/src/utils.ts"),
        Path("repo/.git/config"),
        Path("repo/node_modules/package/index.js"),
        Path("repo/app/__pycache__/main.pyc"),
        Path("repo/build/output.o"),
    ]

    filtered = filter_files(files)

    assert set(filtered) == {
        Path("repo/README.md"),
        Path("repo/src/main.py"),
        Path("repo/src/utils.ts"),
    }


def test_filter_files_ignores_suffix_case() -> None:
    files = [
        Path("repo/cache/file.pyc"),
        Path("repo/cache/file.PYC"),
        Path("repo/src/main.py"),
    ]

    filtered = filter_files(files)

    assert filtered == [
        Path("repo/src/main.py"),
    ]


def test_filter_files_empty() -> None:
    assert filter_files([]) == []
