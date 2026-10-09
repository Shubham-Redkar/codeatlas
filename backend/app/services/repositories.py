import asyncio
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.parse import urlparse

from sqlalchemy.ext.asyncio import AsyncSession

from ..core.exceptions import GitCloneError
from ..database.models import Repository
from ..database.repositories import create_repository
from ..ingestion import FileChangeType, clone_repository
from .indexing import index_repository


def repository_name_from_url(
    url: str,
) -> str:
    """
    Extract a repository name from a Git repository URL.
    """
    path = urlparse(url).path.rstrip("/")

    if not path:
        return "repository"

    name = Path(path).name

    if name.endswith(".git"):
        name = name[:-4]

    return name or "repository"


async def ingest_repository(
    session: AsyncSession,
    url: str,
    branch: str | None = None,
) -> tuple[Repository, int]:
    """
    Clone, index, and persist a Git repository.
    """
    repository_name = repository_name_from_url(url)

    with TemporaryDirectory(prefix="codeatlas-") as temporary_directory:
        repository_path = Path(temporary_directory) / "repository"

        await clone_repository(
            url=url,
            destination=repository_path,
            branch=branch,
        )

        actual_branch = branch or await _get_current_branch(
            repository_path,
        )

        async with session.begin():
            repository = await create_repository(
                session=session,
                name=repository_name,
                url=url,
                branch=actual_branch,
            )

        changes = await index_repository(
            session=session,
            repository=repository,
            repository_path=repository_path,
        )

        file_count = sum(change.change_type is not FileChangeType.DELETED for change in changes)

    return repository, file_count


async def _get_current_branch(
    repository_path: Path,
) -> str:
    """
    Get the currently checked-out Git branch.
    """
    process: asyncio.subprocess.Process | None = None

    try:
        process = await asyncio.create_subprocess_exec(
            "git",
            "-C",
            str(repository_path),
            "branch",
            "--show-current",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        stdout, stderr = await asyncio.wait_for(
            process.communicate(),
            timeout=30.0,
        )

    except TimeoutError as exc:
        if process is not None and process.returncode is None:
            process.kill()
            await process.wait()

        raise GitCloneError(
            "Timed out while determining repository branch.",
        ) from exc

    except asyncio.CancelledError:
        if process is not None and process.returncode is None:
            process.kill()
            await process.wait()
        raise

    except OSError as exc:
        raise GitCloneError(
            "Failed to execute Git while determining repository branch",
        ) from exc

    if process.returncode != 0:
        error = stderr.decode().strip()

        raise GitCloneError(
            f"Failed to determine repository branch: {error}",
        )

    detected_branch = stdout.decode(errors="replace").strip()

    if not detected_branch:
        raise GitCloneError(
            "Repository is not currently checked out to a branch",
        )

    return detected_branch
