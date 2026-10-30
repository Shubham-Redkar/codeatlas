import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import Repository, RepositoryFile, SymbolRelationship
from app.database.repositories import (
    replace_symbol_relationships,
    replace_symbols,
)
from app.parser import RelationshipKind, Symbol, SymbolKind


@pytest.mark.asyncio
async def test_replace_symbol_relationships(
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
        size_bytes=64,
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

    result = await db_session.execute(select(SymbolRelationship))
    persisted_relationships = list(result.scalars().all())

    assert len(persisted_relationships) == 1
    assert persisted_relationships[0].source_symbol_id == source_symbol.id
    assert persisted_relationships[0].target_symbol_id == target_symbol.id
    assert persisted_relationships[0].kind == RelationshipKind.CALLS.value
    assert persisted_relationships[0].line == 2

    await replace_symbol_relationships(
        session=db_session,
        repository_file_id=repository_file.id,
        relationships=[],
    )

    result = await db_session.execute(select(SymbolRelationship))
    assert list(result.scalars().all()) == []


@pytest.mark.asyncio
async def test_get_repository_symbol_relationships(
    db_session: AsyncSession,
) -> None:
    from app.database.repositories import get_repository_symbol_relationships

    repository = Repository(
        name="CodeAtlas",
        url="https://github.com/example/codeatlas.git",
        branch="main",
    )
    other_repository = Repository(
        name="Other",
        url="https://github.com/example/other.git",
        branch="main",
    )
    db_session.add_all([repository, other_repository])
    await db_session.flush()

    files = [
        RepositoryFile(
            repository_id=repository.id,
            path="src/main.py",
            content_hash="a",
            size_bytes=64,
            language="python",
        ),
        RepositoryFile(
            repository_id=repository.id,
            path="src/helpers.py",
            content_hash="b",
            size_bytes=64,
            language="python",
        ),
        RepositoryFile(
            repository_id=other_repository.id,
            path="src/other.py",
            content_hash="c",
            size_bytes=64,
            language="python",
        ),
    ]
    db_session.add_all(files)
    await db_session.flush()

    symbols_by_file = []
    for repository_file, name in zip(
        files,
        ["main_func", "helper_func", "other_func"],
        strict=True,
    ):
        symbols = await replace_symbols(
            session=db_session,
            repository_file_id=repository_file.id,
            symbols=[
                Symbol(
                    name=name,
                    kind=SymbolKind.FUNCTION,
                    start_byte=0,
                    end_byte=10,
                    start_line=1,
                    end_line=1,
                ),
            ],
        )
        symbols_by_file.append(symbols[0])

    main_symbol, helper_symbol, other_symbol = symbols_by_file

    await replace_symbol_relationships(
        session=db_session,
        repository_file_id=files[0].id,
        relationships=[
            (
                main_symbol.id,
                helper_symbol.id,
                RelationshipKind.CALLS.value,
                1,
            ),
            (
                main_symbol.id,
                other_symbol.id,
                RelationshipKind.CALLS.value,
                2,
            ),
        ],
    )

    relationships = await get_repository_symbol_relationships(
        session=db_session,
        repository_id=repository.id,
    )

    assert len(relationships) == 1
    assert relationships[0].source_symbol_id == main_symbol.id
    assert relationships[0].target_symbol_id == helper_symbol.id
