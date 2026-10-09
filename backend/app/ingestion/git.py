import asyncio
from pathlib import Path

from ..core.exceptions import GitCloneError


async def clone_repository(
    url: str,
    destination: Path,
    branch: str | None = None,
) -> Path:
    """
    Clone a Git repository into the given destination.
    """
    destination_exists = await asyncio.to_thread(
        destination.exists,
    )

    if destination_exists:
        raise GitCloneError(
            f"Clone destination already exists: {destination}",
        )

    await asyncio.to_thread(
        destination.parent.mkdir,
        parents=True,
        exist_ok=True,
    )

    command = [
        "git",
        "clone",
        "--depth",
        "1",
        "--single-branch",
    ]

    if branch is not None:
        command.extend(["--branch", branch])

    command.extend([url, str(destination)])

    process: asyncio.subprocess.Process | None = None

    try:
        process = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.PIPE,
        )

        async with asyncio.timeout(300.0):
            _, stderr = await process.communicate()

    except TimeoutError as exc:
        if process is not None and process.returncode is None:
            process.kill()
            await process.wait()

        raise GitCloneError(
            "Git clone operation timed out after 300 seconds.",
        ) from exc

    except asyncio.CancelledError:
        if process is not None and process.returncode is None:
            process.kill()
            await process.wait()
        raise

    except OSError as exc:
        raise GitCloneError(
            f"Failed to execute Git while cloning repository: {url}",
        ) from exc

    if process.returncode != 0:
        error = stderr.decode(errors="replace").strip()

        raise GitCloneError(
            f"Failed to clone repository '{url}': {error}",
        )

    return destination
