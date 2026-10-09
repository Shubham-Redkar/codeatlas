from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.core.exceptions import GitCloneError
from app.ingestion import FileChangeType
from app.services import repositories as service


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        ("https://github.com/user/my-project.git", "my-project"),
        ("https://github.com/user/my-project", "my-project"),
        ("https://github.com/user/my-project.git/", "my-project"),
        ("https://github.com/user/", "user"),
        ("https://github.com/user", "user"),
        ("", "repository"),
    ],
)
def test_repository_name_from_url(url, expected):
    assert service.repository_name_from_url(url) == expected


class FakeProcess:
    def __init__(
        self,
        stdout: bytes = b"main\n",
        stderr: bytes = b"",
        returncode: int | None = 0,
    ) -> None:
        self.stdout = stdout
        self.stderr = stderr
        self.returncode = returncode
        self.killed = False
        self.waited = False

    async def communicate(self) -> tuple[bytes, bytes]:
        return self.stdout, self.stderr

    def kill(self) -> None:
        self.killed = True
        self.returncode = -9

    async def wait(self) -> None:
        self.waited = True


@pytest.mark.asyncio
async def test_get_current_branch_success(monkeypatch, tmp_path):
    process = FakeProcess(stdout=b"feature/search\n")

    create_process = AsyncMock(return_value=process)
    monkeypatch.setattr(
        service.asyncio,
        "create_subprocess_exec",
        create_process,
    )

    result = await service._get_current_branch(tmp_path)

    assert result == "feature/search"
    create_process.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_current_branch_git_failure(monkeypatch, tmp_path):
    process = FakeProcess(
        stderr=b"not a git repository",
        returncode=128,
    )
    monkeypatch.setattr(
        service.asyncio,
        "create_subprocess_exec",
        AsyncMock(return_value=process),
    )

    with pytest.raises(GitCloneError, match="not a git repository"):
        await service._get_current_branch(tmp_path)


@pytest.mark.asyncio
async def test_get_current_branch_empty_output(monkeypatch, tmp_path):
    process = FakeProcess(stdout=b"")
    monkeypatch.setattr(
        service.asyncio,
        "create_subprocess_exec",
        AsyncMock(return_value=process),
    )

    with pytest.raises(GitCloneError, match="not currently checked out"):
        await service._get_current_branch(tmp_path)


@pytest.mark.asyncio
async def test_get_current_branch_os_error(monkeypatch, tmp_path):
    create_process = AsyncMock(
        side_effect=OSError("git executable not found"),
    )
    monkeypatch.setattr(
        service.asyncio,
        "create_subprocess_exec",
        create_process,
    )

    with pytest.raises(GitCloneError, match="Failed to execute Git"):
        await service._get_current_branch(tmp_path)


@pytest.mark.asyncio
async def test_get_current_branch_timeout_kills_process(
    monkeypatch,
    tmp_path,
):
    process = FakeProcess()
    process.returncode = None

    async def timeout_communicate():
        raise TimeoutError

    process.communicate = timeout_communicate

    monkeypatch.setattr(
        service.asyncio,
        "create_subprocess_exec",
        AsyncMock(return_value=process),
    )

    with pytest.raises(GitCloneError, match="Timed out"):
        await service._get_current_branch(tmp_path)

    assert process.killed
    assert process.waited


class FakeTransaction:
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, traceback):
        return False


def make_session():
    session = MagicMock()
    session.begin.return_value = FakeTransaction()
    return session


@pytest.mark.asyncio
async def test_ingest_repository_success(monkeypatch):
    session = make_session()
    repository = SimpleNamespace(name="demo")
    changes = [
        SimpleNamespace(change_type=FileChangeType.NEW),
        SimpleNamespace(change_type=FileChangeType.CHANGED),
        SimpleNamespace(change_type=FileChangeType.DELETED),
    ]

    clone = AsyncMock()
    create = AsyncMock(return_value=repository)
    index = AsyncMock(return_value=changes)

    monkeypatch.setattr(service, "clone_repository", clone)
    monkeypatch.setattr(service, "create_repository", create)
    monkeypatch.setattr(service, "index_repository", index)

    result_repository, file_count = await service.ingest_repository(
        session=session,
        url="https://github.com/user/demo.git",
        branch="main",
    )

    assert result_repository is repository
    assert file_count == 2

    clone.assert_awaited_once()
    create.assert_awaited_once_with(
        session=session,
        name="demo",
        url="https://github.com/user/demo.git",
        branch="main",
    )
    index.assert_awaited_once()


@pytest.mark.asyncio
async def test_ingest_repository_clone_failure(monkeypatch):
    session = make_session()

    clone = AsyncMock(
        side_effect=GitCloneError("clone failed"),
    )
    create = AsyncMock()
    index = AsyncMock()

    monkeypatch.setattr(service, "clone_repository", clone)
    monkeypatch.setattr(service, "create_repository", create)
    monkeypatch.setattr(service, "index_repository", index)

    with pytest.raises(GitCloneError, match="clone failed"):
        await service.ingest_repository(
            session=session,
            url="https://github.com/user/demo.git",
            branch="main",
        )

    create.assert_not_awaited()
    index.assert_not_awaited()


@pytest.mark.asyncio
async def test_ingest_repository_detects_branch_when_unspecified(
    monkeypatch,
):
    session = make_session()
    repository = SimpleNamespace(name="demo")

    monkeypatch.setattr(
        service,
        "clone_repository",
        AsyncMock(),
    )
    monkeypatch.setattr(
        service,
        "_get_current_branch",
        AsyncMock(return_value="develop"),
    )
    create = AsyncMock(return_value=repository)
    monkeypatch.setattr(service, "create_repository", create)
    monkeypatch.setattr(
        service,
        "index_repository",
        AsyncMock(return_value=[]),
    )

    result_repository, file_count = await service.ingest_repository(
        session=session,
        url="https://github.com/user/demo.git",
    )

    assert result_repository is repository
    assert file_count == 0
    assert create.await_args is not None
    assert create.await_args.kwargs["branch"] == "develop"


@pytest.mark.asyncio
async def test_ingest_repository_indexing_failure_propagates(
    monkeypatch,
):
    session = make_session()
    repository = SimpleNamespace(name="demo")

    monkeypatch.setattr(
        service,
        "clone_repository",
        AsyncMock(),
    )
    monkeypatch.setattr(
        service,
        "create_repository",
        AsyncMock(return_value=repository),
    )
    monkeypatch.setattr(
        service,
        "index_repository",
        AsyncMock(side_effect=RuntimeError("index failed")),
    )

    with pytest.raises(RuntimeError, match="index failed"):
        await service.ingest_repository(
            session=session,
            url="https://github.com/user/demo.git",
            branch="main",
        )
