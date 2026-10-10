import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import Repository, RepositoryFile, Symbol


@pytest.mark.asyncio
async def test_create_symbol(db_session: AsyncSession) -> None:
    repository = Repository(
        name="CodeAtlas",
        url="https://github.com/example/codeatlas.git",
        branch="main",
    )
    db_session.add(repository)
    await db_session.flush()

    repository_file = RepositoryFile(
        repository_id=repository.id,
        path="src/main.py",
        content_hash="abc123",
        size_bytes=128,
        language="python",
    )
    db_session.add(repository_file)
    await db_session.flush()

    symbol = Symbol(
        repository_file_id=repository_file.id,
        name="UserService",
        kind="class",
        start_byte=0,
        end_byte=120,
        start_line=1,
        end_line=8,
        parameters=[],
        return_type=None,
        bases=["BaseService"],
        parent_name=None,
    )
    db_session.add(symbol)
    await db_session.flush()

    result = await db_session.execute(select(Symbol).where(Symbol.id == symbol.id))
    persisted_symbol = result.scalar_one()

    assert persisted_symbol.repository_file_id == repository_file.id
    assert persisted_symbol.name == "UserService"
    assert persisted_symbol.kind == "class"
    assert persisted_symbol.start_byte == 0
    assert persisted_symbol.end_byte == 120
    assert persisted_symbol.start_line == 1
    assert persisted_symbol.end_line == 8
    assert persisted_symbol.parameters == []
    assert persisted_symbol.return_type is None
    assert persisted_symbol.bases == ["BaseService"]
    assert persisted_symbol.parent_name is None


@pytest.mark.asyncio
async def test_create_symbol_with_optional_fields_unset(
    db_session: AsyncSession,
) -> None:
    repository = Repository(
        name="CodeAtlas",
        url="https://github.com/example/codeatlas.git",
        branch="main",
    )
    db_session.add(repository)
    await db_session.flush()

    repository_file = RepositoryFile(
        repository_id=repository.id,
        path="src/main.py",
        content_hash="abc123",
        size_bytes=32,
        language="python",
    )
    db_session.add(repository_file)
    await db_session.flush()

    symbol = Symbol(
        repository_file_id=repository_file.id,
        name="get_user",
        kind="function",
        start_byte=0,
        end_byte=32,
        start_line=1,
        end_line=2,
    )
    db_session.add(symbol)
    await db_session.flush()

    result = await db_session.execute(select(Symbol).where(Symbol.id == symbol.id))
    persisted_symbol = result.scalar_one()

    assert persisted_symbol.parameters == []
    assert persisted_symbol.return_type is None
    assert persisted_symbol.bases == []
    assert persisted_symbol.parent_name is None
