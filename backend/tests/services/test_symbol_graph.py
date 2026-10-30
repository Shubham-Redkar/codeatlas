from pathlib import Path
from uuid import uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import Repository, RepositoryFile
from app.database.models import Symbol as SymbolRecord
from app.database.repositories import replace_symbol_relationships, replace_symbols
from app.graph import SymbolEdge
from app.parser import RelationshipKind, Symbol, SymbolKind
from app.services import (
    get_repository_symbol_graph,
    get_symbol_impact,
    index_repository,
)


@pytest.mark.asyncio
async def test_get_repository_symbol_graph(
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
        content_hash="main-hash",
        size_bytes=100,
        language="python",
    )
    db_session.add(repository_file)
    await db_session.flush()

    persisted_symbols = await replace_symbols(
        session=db_session,
        repository_file_id=repository_file.id,
        symbols=[
            Symbol(
                name="create_user",
                kind=SymbolKind.FUNCTION,
                start_byte=0,
                end_byte=30,
                start_line=1,
                end_line=2,
            ),
            Symbol(
                name="save_user",
                kind=SymbolKind.FUNCTION,
                start_byte=31,
                end_byte=60,
                start_line=4,
                end_line=5,
            ),
        ],
    )
    source_symbol, target_symbol = persisted_symbols

    await replace_symbol_relationships(
        session=db_session,
        repository_file_id=repository_file.id,
        relationships=[
            (
                source_symbol.id,
                target_symbol.id,
                RelationshipKind.CALLS.value,
                2,
            ),
        ],
    )

    graph = await get_repository_symbol_graph(
        session=db_session,
        repository_id=repository.id,
    )

    assert graph.edges == (
        SymbolEdge(
            source=source_symbol.id,
            target=target_symbol.id,
            kind=RelationshipKind.CALLS.value,
        ),
    )
    assert graph.get_relationships(
        source_symbol.id,
        RelationshipKind.CALLS.value,
    ) == frozenset({target_symbol.id})


@pytest.mark.asyncio
async def test_get_symbol_impact_returns_transitive_callers(
    db_session: AsyncSession,
) -> None:
    from app.services.symbol_graph import get_symbol_impact

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
        content_hash="main-hash",
        size_bytes=100,
        language="python",
    )
    db_session.add(repository_file)
    await db_session.flush()

    symbols = await replace_symbols(
        session=db_session,
        repository_file_id=repository_file.id,
        symbols=[
            Symbol(
                name="register_account",
                kind=SymbolKind.FUNCTION,
                start_byte=0,
                end_byte=20,
                start_line=1,
                end_line=2,
            ),
            Symbol(
                name="create_user",
                kind=SymbolKind.FUNCTION,
                start_byte=21,
                end_byte=40,
                start_line=4,
                end_line=5,
            ),
            Symbol(
                name="save_user",
                kind=SymbolKind.FUNCTION,
                start_byte=41,
                end_byte=60,
                start_line=7,
                end_line=8,
            ),
        ],
    )
    register_symbol, create_symbol, save_symbol = symbols

    await replace_symbol_relationships(
        session=db_session,
        repository_file_id=repository_file.id,
        relationships=[
            (
                register_symbol.id,
                create_symbol.id,
                RelationshipKind.CALLS.value,
                2,
            ),
            (
                create_symbol.id,
                save_symbol.id,
                RelationshipKind.CALLS.value,
                5,
            ),
        ],
    )

    impacted_symbols = await get_symbol_impact(
        session=db_session,
        repository_id=repository.id,
        symbol_id=save_symbol.id,
    )

    assert impacted_symbols == frozenset({register_symbol.id, create_symbol.id})


@pytest.mark.asyncio
async def test_get_symbol_impact_returns_empty_for_unknown_symbol(
    db_session: AsyncSession,
) -> None:
    repository = Repository(
        name="CodeAtlas",
        url="https://github.com/example/codeatlas.git",
        branch="main",
    )
    db_session.add(repository)
    await db_session.flush()

    unknown_symbol_id = uuid4()

    impacted_symbols = await get_symbol_impact(
        session=db_session,
        repository_id=repository.id,
        symbol_id=unknown_symbol_id,
    )

    assert impacted_symbols == frozenset()


@pytest.mark.asyncio
async def test_get_symbol_impact_does_not_cross_repository_boundaries(
    db_session: AsyncSession,
) -> None:
    repository_a = Repository(
        name="Repository A",
        url="https://github.com/example/repository-a.git",
        branch="main",
    )
    repository_b = Repository(
        name="Repository B",
        url="https://github.com/example/repository-b.git",
        branch="main",
    )
    db_session.add_all([repository_a, repository_b])
    await db_session.flush()

    repository_file_a = RepositoryFile(
        repository_id=repository_a.id,
        path="src/main.py",
        content_hash="hash-a",
        size_bytes=100,
        language="python",
    )
    repository_file_b = RepositoryFile(
        repository_id=repository_b.id,
        path="src/main.py",
        content_hash="hash-b",
        size_bytes=100,
        language="python",
    )
    db_session.add_all([repository_file_a, repository_file_b])
    await db_session.flush()

    symbols_a = await replace_symbols(
        session=db_session,
        repository_file_id=repository_file_a.id,
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

    symbols_b = await replace_symbols(
        session=db_session,
        repository_file_id=repository_file_b.id,
        symbols=[
            Symbol(
                name="create_user",
                kind=SymbolKind.FUNCTION,
                start_byte=0,
                end_byte=20,
                start_line=1,
                end_line=2,
            ),
            Symbol(
                name="save_user",
                kind=SymbolKind.FUNCTION,
                start_byte=21,
                end_byte=40,
                start_line=4,
                end_line=5,
            ),
        ],
    )

    create_symbol, save_symbol = symbols_b

    await replace_symbol_relationships(
        session=db_session,
        repository_file_id=repository_file_b.id,
        relationships=[
            (
                create_symbol.id,
                save_symbol.id,
                RelationshipKind.CALLS.value,
                2,
            ),
        ],
    )

    impacted_symbols = await get_symbol_impact(
        session=db_session,
        repository_id=repository_a.id,
        symbol_id=symbols_a[0].id,
    )

    assert impacted_symbols == frozenset()


@pytest.mark.asyncio
async def test_cross_file_indexing_integrates_with_symbol_impact(
    db_session: AsyncSession,
    tmp_path: Path,
) -> None:
    source_directory = tmp_path / "src"
    source_directory.mkdir()

    (source_directory / "routes.py").write_text(
        "from src.services import save_user\n\ndef create_user():\n    save_user()\n",
        encoding="utf-8",
    )

    (source_directory / "services.py").write_text(
        "def save_user():\n    pass\n",
        encoding="utf-8",
    )

    repository = Repository(
        name="CodeAtlas",
        url="https://github.com/example/codeatlas.git",
        branch="main",
    )
    db_session.add(repository)
    await db_session.flush()
    await db_session.commit()

    await index_repository(
        session=db_session,
        repository=repository,
        repository_path=tmp_path,
    )

    result = await db_session.execute(
        select(SymbolRecord)
        .join(RepositoryFile)
        .where(RepositoryFile.repository_id == repository.id)
    )

    symbols_by_name = {symbol.name: symbol for symbol in result.scalars().all()}

    assert "create_user" in symbols_by_name
    assert "save_user" in symbols_by_name

    impacted_symbols = await get_symbol_impact(
        session=db_session,
        repository_id=repository.id,
        symbol_id=symbols_by_name["save_user"].id,
    )

    assert impacted_symbols == frozenset(
        {
            symbols_by_name["create_user"].id,
        }
    )
