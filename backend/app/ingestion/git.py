import asyncio
from pathlib import Path

from ..exceptions import GitCloneError


async def clone_repository(
    url: str,
    branch: str,
    destination: Path,
) -> Path:
    """Clone a Git Repository into the given destination."""

    destination.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    process = await asyncio.create_subprocess_exec(
        "git",
        "clone",
        "--branch",
        branch,
        "--single-branch",
        url,
        str(destination),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    _, stderr = await process.communicate()

    if process.returncode != 0:
        error = stderr.decode().strip()

        raise GitCloneError(f"Failed to clone repository: {error}")

    return destination
