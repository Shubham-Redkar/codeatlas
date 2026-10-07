from pathlib import Path

from app.ingestion.files import discover_files


def test_discover_files(tmp_path: Path) -> None:
    """
    Discover files recursively inside a repository.
    """

    readme = tmp_path / "README.md"
    readme.write_text("# CodeAtlas", encoding="utf-8")

    app_directory = tmp_path / "app"
    app_directory.mkdir()

    main = app_directory / "main.py"
    main.write_text("print('hello')", encoding="utf-8")

    services_directory = app_directory / "services"
    services_directory.mkdir()

    user = services_directory / "user.py"
    user.write_text("def user(): pass", encoding="utf-8")

    files = discover_files(tmp_path)

    assert set(files) == {
        readme,
        main,
        user,
    }


def test_discover_files_empty_repository(tmp_path: Path) -> None:
    """
    Return an empty list when the repository contains no files.
    """

    files = discover_files(tmp_path)

    assert files == []


def test_discover_files_nested_directories(tmp_path: Path) -> None:
    """
    Discover files at multiple levels of nesting.
    """

    nested_directory = tmp_path / "src" / "services" / "users"
    nested_directory.mkdir(parents=True)

    user_file = nested_directory / "user.py"
    user_file.write_text(
        "def get_user(): pass",
        encoding="utf-8",
    )

    config_file = tmp_path / "config.py"
    config_file.write_text(
        "DEBUG = True",
        encoding="utf-8",
    )

    files = discover_files(tmp_path)

    assert set(files) == {
        user_file,
        config_file,
    }
