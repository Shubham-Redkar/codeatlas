import subprocess
from pathlib import Path

import pytest

from app.exceptions import GitCloneError
from app.ingestion.git import clone_repository


def create_test_repository(path: Path) -> None:
    """Create a small local Git repository for testing."""

    subprocess.run(
        ["git", "init", "-b", "main"],
        cwd=path,
        check=True,
        capture_output=True,
    )

    subprocess.run(
        ["git", "config", "user.name", "CodeAtlas Test"],
        cwd=path,
        check=True,
        capture_output=True,
    )

    subprocess.run(
        ["git", "config", "user.email", "test@codeatlas.local"],
        cwd=path,
        check=True,
        capture_output=True,
    )

    (path / "README.md").write_text(
        "# Test Repository\n",
        encoding="utf-8",
    )

    subprocess.run(
        ["git", "add", "README.md"],
        cwd=path,
        check=True,
        capture_output=True,
    )

    subprocess.run(
        ["git", "commit", "-m", "initial commit"],
        cwd=path,
        check=True,
        capture_output=True,
    )


@pytest.mark.asyncio
async def test_clone_repository(tmp_path: Path) -> None:
    """Clone a Git repository into the requested destination."""

    source = tmp_path / "source"
    destination = tmp_path / "cloned"

    source.mkdir()

    create_test_repository(source)

    result = await clone_repository(
        url=str(source),
        branch="main",
        destination=destination,
    )

    assert result == destination
    assert destination.exists()
    assert (destination / "README.md").exists()
    assert (destination / "README.md").read_text(encoding="utf-8") == ("# Test Repository\n")
    assert (destination / ".git").exists()


@pytest.mark.asyncio
async def test_clone_repository_invalid_url(tmp_path: Path) -> None:
    """Raise GitCloneError when cloning fails."""

    destination = tmp_path / "cloned"

    with pytest.raises(GitCloneError):
        await clone_repository(
            url="/this/repository/does/not/exist",
            branch="main",
            destination=destination,
        )


@pytest.mark.asyncio
async def test_clone_repository_invalid_branch(tmp_path: Path) -> None:
    """Raise GitCloneError when the requested branch does not exist."""

    source = tmp_path / "source"
    destination = tmp_path / "cloned"

    source.mkdir()
    create_test_repository(source)

    with pytest.raises(GitCloneError):
        await clone_repository(
            url=str(source),
            branch="does-not-exist",
            destination=destination,
        )
