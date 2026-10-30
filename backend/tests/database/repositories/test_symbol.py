import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import Repository, RepositoryFile
from app.database.models import Symbol as SymbolRecord
from app.database.repositories import get_repository_symbols, replace_symbols
from app.parser.symbols import Symbol, SymbolKind


@pytest.mark.asyncio
async def test_replace_symbols(
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
        size_bytes=128,
        language="python",
    )
    db_session.add(repository_file)
    await db_session.flush()

    symbols = [
        Symbol(
            name="UserService",
            kind=SymbolKind.CLASS,
            start_byte=0,
            end_byte=120,
            start_line=1,
            end_line=8,
            bases=("BaseService",),
        ),
        Symbol(
            name="get_user",
            kind=SymbolKind.FUNCTION,
            start_byte=20,
            end_byte=60,
            start_line=3,
            end_line=5,
            parameters=("user_id",),
            return_type="User",
            parent_name="UserService",
        ),
    ]

    await replace_symbols(
        session=db_session,
        repository_file_id=repository_file.id,
        symbols=symbols,
    )

    result = await db_session.execute(
        select(SymbolRecord)
        .where(SymbolRecord.repository_file_id == repository_file.id)
        .order_by(SymbolRecord.start_byte)
    )
    persisted = list(result.scalars())

    assert len(persisted) == 2
    assert persisted[0].name == "UserService"
    assert persisted[0].kind == "class"
    assert persisted[0].bases == ["BaseService"]
    assert persisted[0].parameters == []
    assert persisted[1].name == "get_user"
    assert persisted[1].kind == "function"
    assert persisted[1].parameters == ["user_id"]
    assert persisted[1].return_type == "User"
    assert persisted[1].parent_name == "UserService"


@pytest.mark.asyncio
async def test_replace_symbols_removes_previous_symbols(
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

    await replace_symbols(
        session=db_session,
        repository_file_id=repository_file.id,
        symbols=[
            Symbol(
                name="old_function",
                kind=SymbolKind.FUNCTION,
                start_byte=0,
                end_byte=10,
                start_line=1,
                end_line=1,
            )
        ],
    )

    await replace_symbols(
        session=db_session,
        repository_file_id=repository_file.id,
        symbols=[
            Symbol(
                name="new_function",
                kind=SymbolKind.FUNCTION,
                start_byte=0,
                end_byte=20,
                start_line=1,
                end_line=2,
            )
        ],
    )

    result = await db_session.execute(
        select(SymbolRecord).where(SymbolRecord.repository_file_id == repository_file.id)
    )
    persisted = list(result.scalars())

    assert len(persisted) == 1
    assert persisted[0].name == "new_function"


@pytest.mark.asyncio
async def test_replace_symbols_with_empty_list_clears_symbols(
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

    await replace_symbols(
        session=db_session,
        repository_file_id=repository_file.id,
        symbols=[
            Symbol(
                name="old_function",
                kind=SymbolKind.FUNCTION,
                start_byte=0,
                end_byte=10,
                start_line=1,
                end_line=1,
            )
        ],
    )

    await replace_symbols(
        session=db_session,
        repository_file_id=repository_file.id,
        symbols=[],
    )

    result = await db_session.execute(
        select(SymbolRecord).where(SymbolRecord.repository_file_id == repository_file.id)
    )

    assert list(result.scalars()) == []


@pytest.mark.asyncio
async def test_get_repository_symbols_returns_symbols_from_all_files(
    db_session: AsyncSession,
) -> None:
    repository = Repository(
        name="CodeAtlas",
        url="https://github.com/example/codeatlas.git",
        branch="main",
    )
    db_session.add(repository)
    await db_session.flush()

    first_file = RepositoryFile(
        repository_id=repository.id,
        path="src/first.py",
        content_hash="first-hash",
        size_bytes=32,
        language="python",
    )
    second_file = RepositoryFile(
        repository_id=repository.id,
        path="src/second.py",
        content_hash="second-hash",
        size_bytes=32,
        language="python",
    )
    db_session.add_all([first_file, second_file])
    await db_session.flush()

    await replace_symbols(
        session=db_session,
        repository_file_id=first_file.id,
        symbols=[
            Symbol(
                name="create_user",
                kind=SymbolKind.FUNCTION,
                start_byte=0,
                end_byte=20,
                start_line=1,
                end_line=2,
            ),
        ],
    )

    await replace_symbols(
        session=db_session,
        repository_file_id=second_file.id,
        symbols=[
            Symbol(
                name="save_user",
                kind=SymbolKind.FUNCTION,
                start_byte=0,
                end_byte=20,
                start_line=1,
                end_line=2,
            ),
        ],
    )

    persisted = await get_repository_symbols(
        session=db_session,
        repository_id=repository.id,
    )

    assert {symbol.name for symbol in persisted} == {
        "create_user",
        "save_user",
    }
    assert {symbol.repository_file_id for symbol in persisted} == {
        first_file.id,
        second_file.id,
    }
