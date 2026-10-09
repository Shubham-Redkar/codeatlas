import asyncio
import subprocess
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.exceptions import GitCloneError
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


@pytest.mark.asyncio
async def test_clone_repository_destination_exists(
    tmp_path: Path,
) -> None:
    destination = tmp_path / "existing"
    destination.mkdir()

    with pytest.raises(GitCloneError, match="destination already exists"):
        await clone_repository(
            url="https://example.com/repo.git",
            destination=destination,
        )


@pytest.mark.asyncio
async def test_clone_repository_passes_branch_to_git(
    tmp_path: Path,
) -> None:
    destination = tmp_path / "cloned"
    process = MagicMock()
    process.returncode = 0
    process.communicate = AsyncMock(return_value=(b"", b""))

    with (
        patch(
            "app.ingestion.git.asyncio.create_subprocess_exec",
            new=AsyncMock(return_value=process),
        ) as create_process,
        patch(
            "app.ingestion.git.asyncio.to_thread",
            new=AsyncMock(return_value=False),
        ),
    ):
        result = await clone_repository(
            url="https://example.com/repo.git",
            destination=destination,
            branch="develop",
        )

    assert result == destination
    assert create_process.await_args is not None
    args = create_process.await_args.args
    assert "--branch" in args
    assert args[args.index("--branch") + 1] == "develop"


@pytest.mark.asyncio
async def test_clone_repository_without_branch(
    tmp_path: Path,
) -> None:
    destination = tmp_path / "cloned"
    process = MagicMock()
    process.returncode = 0
    process.communicate = AsyncMock(return_value=(b"", b""))

    with (
        patch(
            "app.ingestion.git.asyncio.create_subprocess_exec",
            new=AsyncMock(return_value=process),
        ) as create_process,
        patch(
            "app.ingestion.git.asyncio.to_thread",
            new=AsyncMock(return_value=False),
        ),
    ):
        await clone_repository(
            url="https://example.com/repo.git",
            destination=destination,
        )

    assert create_process.await_args is not None
    args = create_process.await_args.args
    assert "--branch" not in args


@pytest.mark.asyncio
async def test_clone_repository_os_error(
    tmp_path: Path,
) -> None:
    destination = tmp_path / "cloned"

    with (
        patch(
            "app.ingestion.git.asyncio.to_thread",
            new=AsyncMock(return_value=False),
        ),
        patch(
            "app.ingestion.git.asyncio.create_subprocess_exec",
            new=AsyncMock(side_effect=OSError("git not found")),
        ),
        pytest.raises(
            GitCloneError,
            match="Failed to execute Git while cloning repository",
        ),
    ):
        await clone_repository(
            url="https://example.com/repo.git",
            destination=destination,
        )


@pytest.mark.asyncio
async def test_clone_repository_timeout_kills_process(
    tmp_path: Path,
) -> None:
    destination = tmp_path / "cloned"
    process = MagicMock()
    process.returncode = None
    process.communicate = AsyncMock(side_effect=TimeoutError)
    process.kill = MagicMock()
    process.wait = AsyncMock()

    with (
        patch(
            "app.ingestion.git.asyncio.to_thread",
            new=AsyncMock(return_value=False),
        ),
        patch(
            "app.ingestion.git.asyncio.create_subprocess_exec",
            new=AsyncMock(return_value=process),
        ),
        patch("app.ingestion.git.asyncio.timeout") as mock_timeout,
    ):
        mock_timeout.return_value.__aenter__.return_value = None
        mock_timeout.return_value.__aexit__.side_effect = lambda exc_type, exc, tb: False

        with pytest.raises(GitCloneError, match="timed out"):
            await clone_repository(
                url="https://example.com/repo.git",
                destination=destination,
            )

    process.kill.assert_called_once()
    process.wait.assert_awaited_once()


@pytest.mark.asyncio
async def test_clone_repository_cancelled_kills_process(
    tmp_path: Path,
) -> None:
    destination = tmp_path / "cloned"
    process = MagicMock()
    process.returncode = None
    process.communicate = AsyncMock(
        side_effect=asyncio.CancelledError,
    )
    process.kill = MagicMock()
    process.wait = AsyncMock()

    with (
        patch(
            "app.ingestion.git.asyncio.to_thread",
            new=AsyncMock(return_value=False),
        ),
        patch(
            "app.ingestion.git.asyncio.create_subprocess_exec",
            new=AsyncMock(return_value=process),
        ),
        pytest.raises(asyncio.CancelledError),
    ):
        await clone_repository(
            url="https://example.com/repo.git",
            destination=destination,
        )

    process.kill.assert_called_once()
    process.wait.assert_awaited_once()


@pytest.mark.asyncio
async def test_clone_repository_cancelled_after_process_exits(
    tmp_path: Path,
) -> None:
    destination = tmp_path / "cloned"
    process = MagicMock()
    process.returncode = 1
    process.communicate = AsyncMock(
        side_effect=asyncio.CancelledError,
    )
    process.kill = MagicMock()
    process.wait = AsyncMock()

    with (
        patch(
            "app.ingestion.git.asyncio.to_thread",
            new=AsyncMock(return_value=False),
        ),
        patch(
            "app.ingestion.git.asyncio.create_subprocess_exec",
            new=AsyncMock(return_value=process),
        ),
        pytest.raises(asyncio.CancelledError),
    ):
        await clone_repository(
            url="https://example.com/repo.git",
            destination=destination,
        )

    process.kill.assert_not_called()
    process.wait.assert_not_awaited()


@pytest.mark.asyncio
async def test_clone_repository_decodes_invalid_stderr(
    tmp_path: Path,
) -> None:
    destination = tmp_path / "cloned"
    process = MagicMock()
    process.returncode = 1
    process.communicate = AsyncMock(
        return_value=(b"", b"\xffinvalid error"),
    )

    with (
        patch(
            "app.ingestion.git.asyncio.to_thread",
            new=AsyncMock(return_value=False),
        ),
        patch(
            "app.ingestion.git.asyncio.create_subprocess_exec",
            new=AsyncMock(return_value=process),
        ),
        pytest.raises(GitCloneError, match="Failed to clone repository"),
    ):
        await clone_repository(
            url="https://example.com/repo.git",
            destination=destination,
        )
