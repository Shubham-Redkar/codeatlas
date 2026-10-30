from pathlib import Path
from unittest.mock import patch

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import FileDependency, Repository, RepositoryFile
from app.database.models import Symbol as SymbolRecord
from app.graph import DependencyGraph
from app.ingestion.indexing import FileChangeType, calculate_file_hash
from app.services.indexing import index_repository


@pytest.mark.asyncio
async def test_index_repository(
    db_session: AsyncSession,
    tmp_path: Path,
) -> None:
    repository = Repository(
        name="CodeAtlas",
        url="https://github.com/example/codeatlas.git",
        branch="main",
    )

    db_session.add(repository)
    await db_session.flush()

    source_directory = tmp_path / "src"
    source_directory.mkdir()

    file_contents = {
        "new.py": "print('new')\n",
        "changed.py": "print('changed')\n",
        "unchanged.py": "print('unchanged')\n",
        "app.js": "console.log('hello');\n",
    }

    for filename, content in file_contents.items():
        (source_directory / filename).write_text(
            content,
            encoding="utf-8",
        )

    unchanged_file = source_directory / "unchanged.py"
    unchanged_hash = calculate_file_hash(unchanged_file)

    db_session.add_all(
        [
            RepositoryFile(
                repository_id=repository.id,
                path="src/changed.py",
                content_hash="old-hash",
                size_bytes=1,
                language="python",
            ),
            RepositoryFile(
                repository_id=repository.id,
                path="src/unchanged.py",
                content_hash=unchanged_hash,
                size_bytes=unchanged_file.stat().st_size,
                language="python",
            ),
            RepositoryFile(
                repository_id=repository.id,
                path="src/deleted.py",
                content_hash="deleted-hash",
                size_bytes=1,
            ),
        ]
    )
    await db_session.flush()

    await db_session.commit()

    changes = await index_repository(
        session=db_session,
        repository=repository,
        repository_path=tmp_path,
    )

    changes_by_path = {change.path: change.change_type for change in changes}

    assert changes_by_path == {
        "src/app.js": FileChangeType.NEW,
        "src/changed.py": FileChangeType.CHANGED,
        "src/deleted.py": FileChangeType.DELETED,
        "src/new.py": FileChangeType.NEW,
        "src/unchanged.py": FileChangeType.UNCHANGED,
    }

    result = await db_session.execute(
        select(RepositoryFile)
        .where(RepositoryFile.repository_id == repository.id)
        .order_by(RepositoryFile.path)
    )
    indexed_files = {file.path: file for file in result.scalars()}

    assert set(indexed_files) == {
        "src/app.js",
        "src/changed.py",
        "src/new.py",
        "src/unchanged.py",
    }

    expected_files = {
        "src/app.js": (
            source_directory / "app.js",
            "javascript",
        ),
        "src/changed.py": (
            source_directory / "changed.py",
            "python",
        ),
        "src/new.py": (
            source_directory / "new.py",
            "python",
        ),
    }

    for relative_path, (file_path, language) in expected_files.items():
        indexed_file = indexed_files[relative_path]

        assert indexed_file.content_hash == calculate_file_hash(file_path)
        assert indexed_file.size_bytes == file_path.stat().st_size
        assert indexed_file.language == language

    unchanged_record = indexed_files["src/unchanged.py"]

    assert unchanged_record.content_hash == unchanged_hash
    assert unchanged_record.size_bytes == unchanged_file.stat().st_size
    assert unchanged_record.language == "python"

    assert "src/deleted.py" not in indexed_files


@pytest.mark.asyncio
async def test_index_repository_persists_symbols(
    db_session: AsyncSession,
    tmp_path: Path,
) -> None:
    repository = Repository(
        name="CodeAtlas",
        url="https://github.com/example/codeatlas.git",
        branch="main",
    )
    db_session.add(repository)
    await db_session.flush()
    await db_session.commit()

    source_directory = tmp_path / "src"
    source_directory.mkdir()
    source_file = source_directory / "main.py"
    source_file.write_text(
        "class UserService:\n"
        "    def get_user(self, user_id: int) -> str:\n"
        "        return str(user_id)\n",
        encoding="utf-8",
    )

    await index_repository(
        session=db_session,
        repository=repository,
        repository_path=tmp_path,
    )

    result = await db_session.execute(
        select(SymbolRecord)
        .join(RepositoryFile)
        .where(RepositoryFile.repository_id == repository.id)
        .order_by(SymbolRecord.start_byte)
    )
    symbols = list(result.scalars())

    assert [(symbol.name, symbol.kind) for symbol in symbols] == [
        ("UserService", "class"),
        ("get_user", "function"),
    ]
    assert symbols[1].parameters == ["self", "user_id"]
    assert symbols[1].parent_name == "UserService"
    assert symbols[1].return_type == "str"


@pytest.mark.asyncio
async def test_index_repository_replaces_symbols_for_changed_file(
    db_session: AsyncSession,
    tmp_path: Path,
) -> None:
    repository = Repository(
        name="CodeAtlas",
        url="https://github.com/example/codeatlas.git",
        branch="main",
    )
    db_session.add(repository)
    await db_session.flush()
    await db_session.commit()

    source_directory = tmp_path / "src"
    source_directory.mkdir()
    source_file = source_directory / "main.py"
    source_file.write_text(
        "def old_function():\n    pass\n",
        encoding="utf-8",
    )

    await index_repository(
        session=db_session,
        repository=repository,
        repository_path=tmp_path,
    )

    source_file.write_text(
        "def new_function():\n    return 1\n",
        encoding="utf-8",
    )

    changes = await index_repository(
        session=db_session,
        repository=repository,
        repository_path=tmp_path,
    )

    result = await db_session.execute(
        select(SymbolRecord)
        .join(RepositoryFile)
        .where(RepositoryFile.repository_id == repository.id)
    )
    symbols = list(result.scalars())

    assert any(
        change.path == "src/main.py" and change.change_type is FileChangeType.CHANGED
        for change in changes
    )
    assert [symbol.name for symbol in symbols] == ["new_function"]


@pytest.mark.asyncio
async def test_index_repository_preserves_symbols_for_unchanged_file(
    db_session: AsyncSession,
    tmp_path: Path,
) -> None:
    repository = Repository(
        name="CodeAtlas",
        url="https://github.com/example/codeatlas.git",
        branch="main",
    )
    db_session.add(repository)
    await db_session.flush()
    await db_session.commit()

    source_directory = tmp_path / "src"
    source_directory.mkdir()
    source_file = source_directory / "main.py"
    source_file.write_text(
        "def existing_function():\n    pass\n",
        encoding="utf-8",
    )

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
    original_symbols = list(result.scalars())
    original_ids = [symbol.id for symbol in original_symbols]
    await db_session.commit()

    with patch("app.services.indexing.replace_symbols") as replace_mock:
        changes = await index_repository(
            session=db_session,
            repository=repository,
            repository_path=tmp_path,
        )

    result = await db_session.execute(
        select(SymbolRecord)
        .join(RepositoryFile)
        .where(RepositoryFile.repository_id == repository.id)
    )
    current_symbols = list(result.scalars())

    assert any(
        change.path == "src/main.py" and change.change_type is FileChangeType.UNCHANGED
        for change in changes
    )
    assert [symbol.id for symbol in current_symbols] == original_ids
    replace_mock.assert_not_called()


@pytest.mark.asyncio
async def test_index_repository_removes_symbols_for_deleted_file(
    db_session: AsyncSession,
    tmp_path: Path,
) -> None:
    """Remove persisted symbols when their source file is deleted."""
    source_directory = tmp_path / "src"
    source_directory.mkdir()
    source_file = source_directory / "main.py"
    source_file.write_text(
        "def existing_function() -> None:\n    pass\n",
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

    source_file.unlink()

    changes = await index_repository(
        session=db_session,
        repository=repository,
        repository_path=tmp_path,
    )

    assert any(
        change.path == "src/main.py" and change.change_type is FileChangeType.DELETED
        for change in changes
    )

    result = await db_session.execute(
        select(SymbolRecord)
        .join(RepositoryFile)
        .where(RepositoryFile.repository_id == repository.id)
    )
    assert list(result.scalars()) == []


@pytest.mark.asyncio
async def test_index_repository_skips_symbol_extraction_for_unsupported_language(
    db_session: AsyncSession,
    tmp_path: Path,
) -> None:
    """Preserve indexed metadata when a stored language is unsupported."""
    from app.ingestion.indexing import calculate_file_hash

    repository = Repository(
        name="CodeAtlas",
        url="https://github.com/example/codeatlas.git",
        branch="main",
    )
    db_session.add(repository)
    await db_session.flush()

    source_directory = tmp_path / "src"
    source_directory.mkdir()
    source_file = source_directory / "main.go"
    source_file.write_text(
        "package main\nfunc main() {}\n",
        encoding="utf-8",
    )

    db_session.add(
        RepositoryFile(
            repository_id=repository.id,
            path="src/main.go",
            content_hash=calculate_file_hash(source_file),
            size_bytes=source_file.stat().st_size,
            language="go",
        )
    )
    await db_session.commit()

    changes = await index_repository(
        session=db_session,
        repository=repository,
        repository_path=tmp_path,
    )

    assert any(
        change.path == "src/main.go" and change.change_type is FileChangeType.UNCHANGED
        for change in changes
    )

    result = await db_session.execute(
        select(RepositoryFile).where(
            RepositoryFile.repository_id == repository.id,
            RepositoryFile.path == "src/main.go",
        )
    )
    repository_file = result.scalar_one()
    assert repository_file.language == "go"

    result = await db_session.execute(
        select(SymbolRecord).where(
            SymbolRecord.repository_file_id == repository_file.id,
        )
    )
    assert list(result.scalars()) == []


@pytest.mark.asyncio
async def test_index_repository_extracts_imports(
    db_session: AsyncSession,
    tmp_path: Path,
) -> None:
    """Extract imports when indexing a new Python file."""
    repository = Repository(
        name="CodeAtlas",
        url="https://github.com/example/codeatlas.git",
        branch="main",
    )
    db_session.add(repository)
    await db_session.flush()
    await db_session.commit()

    source_directory = tmp_path / "src"
    source_directory.mkdir()
    source_file = source_directory / "main.py"
    source_file.write_text(
        "from app.services import indexing\n",
        encoding="utf-8",
    )

    with patch("app.services.indexing.extract_imports") as extract_imports_mock:
        await index_repository(
            session=db_session,
            repository=repository,
            repository_path=tmp_path,
        )

    extract_imports_mock.assert_called_once()
    args, _ = extract_imports_mock.call_args
    assert args[1] == "python"


@pytest.mark.asyncio
async def test_index_repository_builds_dependency_graph(
    db_session: AsyncSession,
    tmp_path: Path,
) -> None:
    """Persist dependency edges when indexing Python imports."""
    repository = Repository(
        name="CodeAtlas",
        url="https://github.com/example/codeatlas.git",
        branch="main",
    )
    db_session.add(repository)
    await db_session.flush()
    await db_session.commit()

    source_directory = tmp_path / "src"
    source_directory.mkdir()

    (source_directory / "helpers.py").write_text(
        "def helper():\n    pass\n",
        encoding="utf-8",
    )
    (source_directory / "main.py").write_text(
        "from src import helpers\n",
        encoding="utf-8",
    )

    await index_repository(
        session=db_session,
        repository=repository,
        repository_path=tmp_path,
    )

    result = await db_session.execute(
        select(RepositoryFile).where(RepositoryFile.repository_id == repository.id)
    )
    files_by_path = {repository_file.path: repository_file for repository_file in result.scalars()}

    result = await db_session.execute(select(FileDependency))
    dependencies = list(result.scalars())

    assert len(dependencies) == 1
    assert dependencies[0].source_file_id == files_by_path["src/main.py"].id
    assert dependencies[0].target_file_id == files_by_path["src/helpers.py"].id


@pytest.mark.asyncio
async def test_index_repository_includes_unchanged_files_in_graph(
    db_session: AsyncSession,
    tmp_path: Path,
) -> None:
    """Include imports from unchanged files when building the dependency graph."""
    repository = Repository(
        name="CodeAtlas",
        url="https://github.com/example/codeatlas.git",
        branch="main",
    )
    db_session.add(repository)
    await db_session.flush()

    source_directory = tmp_path / "src"
    source_directory.mkdir()

    helper_file = source_directory / "helpers.py"
    helper_file.write_text(
        "def helper():\n    pass\n",
        encoding="utf-8",
    )
    main_file = source_directory / "main.py"
    main_file.write_text(
        "from src import helpers\n",
        encoding="utf-8",
    )

    db_session.add(
        RepositoryFile(
            repository_id=repository.id,
            path="src/main.py",
            content_hash=calculate_file_hash(main_file),
            size_bytes=main_file.stat().st_size,
            language="python",
        )
    )
    await db_session.commit()

    with patch(
        "app.services.indexing.build_python_dependency_graph",
        return_value=DependencyGraph(dependencies=()),
    ) as build_graph_mock:
        changes = await index_repository(
            session=db_session,
            repository=repository,
            repository_path=tmp_path,
        )

    assert (
        next(change for change in changes if change.path == "src/main.py").change_type
        is FileChangeType.UNCHANGED
    )

    imports_by_file = build_graph_mock.call_args.kwargs["imports_by_file"]
    assert "src/main.py" in imports_by_file


@pytest.mark.asyncio
async def test_index_repository_removes_dependencies_for_deleted_file(
    db_session: AsyncSession,
    tmp_path: Path,
) -> None:
    """Remove dependency edges when a referenced file is deleted."""
    repository = Repository(
        name="CodeAtlas",
        url="https://github.com/example/codeatlas.git",
        branch="main",
    )
    db_session.add(repository)
    await db_session.flush()
    await db_session.commit()

    source_directory = tmp_path / "src"
    source_directory.mkdir()

    helper_file = source_directory / "helpers.py"
    helper_file.write_text(
        "def helper():\n    pass\n",
        encoding="utf-8",
    )
    main_file = source_directory / "main.py"
    main_file.write_text(
        "from src import helpers\n",
        encoding="utf-8",
    )

    await index_repository(
        session=db_session,
        repository=repository,
        repository_path=tmp_path,
    )

    result = await db_session.execute(select(FileDependency))
    assert len(list(result.scalars())) == 1
    await db_session.commit()

    helper_file.unlink()

    changes = await index_repository(
        session=db_session,
        repository=repository,
        repository_path=tmp_path,
    )

    assert any(
        change.path == "src/helpers.py" and change.change_type is FileChangeType.DELETED
        for change in changes
    )

    result = await db_session.execute(select(FileDependency))
    assert list(result.scalars()) == []


@pytest.mark.asyncio
async def test_index_repository_persists_symbol_relationships(
    db_session: AsyncSession,
    tmp_path: Path,
) -> None:
    from app.database.models import SymbolRelationship

    source_directory = tmp_path / "src"
    source_directory.mkdir()
    source_file = source_directory / "main.py"
    source_file.write_text(
        "def create_user():\n    save_user()\n\ndef save_user():\n    pass\n",
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
        select(SymbolRelationship)
        .join(
            SymbolRecord,
            SymbolRelationship.source_symbol_id == SymbolRecord.id,
        )
        .where(
            SymbolRecord.name == "create_user",
            SymbolRelationship.kind == "calls",
        )
    )
    relationships = list(result.scalars().all())

    assert len(relationships) == 1
    assert relationships[0].line == 2

    source_result = await db_session.execute(
        select(SymbolRecord).where(SymbolRecord.id == relationships[0].source_symbol_id)
    )
    source_symbol = source_result.scalar_one()

    target_result = await db_session.execute(
        select(SymbolRecord).where(SymbolRecord.id == relationships[0].target_symbol_id)
    )
    target_symbol = target_result.scalar_one()

    assert source_symbol.name == "create_user"
    assert target_symbol.name == "save_user"


@pytest.mark.asyncio
async def test_index_repository_persists_cross_file_symbol_relationships(
    db_session: AsyncSession,
    tmp_path: Path,
) -> None:
    from app.database.models import SymbolRelationship

    source_directory = tmp_path / "src"
    source_directory.mkdir()

    routes_file = source_directory / "routes.py"
    routes_file.write_text(
        "from src.services import save_user\n\ndef create_user():\n    save_user()\n",
        encoding="utf-8",
    )

    services_file = source_directory / "services.py"
    services_file.write_text(
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
        select(SymbolRelationship)
        .join(
            SymbolRecord,
            SymbolRelationship.source_symbol_id == SymbolRecord.id,
        )
        .where(
            SymbolRecord.name == "create_user",
            SymbolRelationship.kind == "calls",
        )
    )
    relationships = list(result.scalars().all())

    assert len(relationships) == 1

    source_result = await db_session.execute(
        select(SymbolRecord).where(
            SymbolRecord.id == relationships[0].source_symbol_id,
        )
    )
    source_symbol = source_result.scalar_one()

    target_result = await db_session.execute(
        select(SymbolRecord).where(
            SymbolRecord.id == relationships[0].target_symbol_id,
        )
    )
    target_symbol = target_result.scalar_one()

    assert source_symbol.name == "create_user"
    assert target_symbol.name == "save_user"
    assert source_symbol.repository_file_id != target_symbol.repository_file_id


@pytest.mark.asyncio
async def test_index_repository_removes_stale_symbol_relationships(
    db_session: AsyncSession,
    tmp_path: Path,
) -> None:
    from app.database.models import SymbolRelationship

    source_directory = tmp_path / "src"
    source_directory.mkdir()
    source_file = source_directory / "main.py"

    source_file.write_text(
        "def create_user():\n    save_user()\n\ndef save_user():\n    pass\n",
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
        select(SymbolRelationship).where(
            SymbolRelationship.kind == "calls",
        )
    )
    assert len(list(result.scalars().all())) == 1

    await db_session.commit()

    source_file.write_text(
        "def create_user():\n    pass\n\ndef save_user():\n    pass\n",
        encoding="utf-8",
    )

    await index_repository(
        session=db_session,
        repository=repository,
        repository_path=tmp_path,
    )

    result = await db_session.execute(
        select(SymbolRelationship).where(
            SymbolRelationship.kind == "calls",
        )
    )
    assert list(result.scalars().all()) == []


@pytest.mark.asyncio
async def test_index_repository_rebuilds_cross_file_relationships_after_target_changes(
    db_session: AsyncSession,
    tmp_path: Path,
) -> None:
    from app.database.models import SymbolRelationship

    source_directory = tmp_path / "src"
    source_directory.mkdir()

    routes_file = source_directory / "routes.py"
    routes_file.write_text(
        "from src.services import save_user\n\ndef create_user():\n    save_user()\n",
        encoding="utf-8",
    )

    services_file = source_directory / "services.py"
    services_file.write_text(
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

    services_file.write_text(
        "def save_user():\n    return True\n",
        encoding="utf-8",
    )

    await index_repository(
        session=db_session,
        repository=repository,
        repository_path=tmp_path,
    )

    result = await db_session.execute(
        select(SymbolRelationship)
        .join(
            SymbolRecord,
            SymbolRelationship.source_symbol_id == SymbolRecord.id,
        )
        .where(
            SymbolRecord.name == "create_user",
            SymbolRelationship.kind == "calls",
        )
    )

    relationships = list(result.scalars().all())

    assert len(relationships) == 1
