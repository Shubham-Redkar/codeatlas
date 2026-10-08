from pathlib import Path

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import Repository, RepositoryFile
from app.ingestion.indexing import calculate_file_hash
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

    new_file = source_directory / "new.py"
    new_file.write_text(
        "print('new')\n",
        encoding="utf-8",
    )

    changed_file = source_directory / "changed.py"
    changed_file.write_text(
        "print('changed')\n",
        encoding="utf-8",
    )

    unchanged_file = source_directory / "unchanged.py"
    unchanged_file.write_text(
        "print('unchanged')\n",
        encoding="utf-8",
    )

    indexed_changed = RepositoryFile(
        repository_id=repository.id,
        path="src/changed.py",
        content_hash="old-hash",
        size_bytes=1,
    )

    unchanged_hash = calculate_file_hash(unchanged_file)
    indexed_unchanged = RepositoryFile(
        repository_id=repository.id,
        path="src/unchanged.py",
        content_hash=unchanged_hash,
        size_bytes=1,
    )

    indexed_deleted = RepositoryFile(
        repository_id=repository.id,
        path="src/deleted.py",
        content_hash="deleted-hash",
        size_bytes=1,
    )

    db_session.add_all(
        [
            indexed_changed,
            indexed_unchanged,
            indexed_deleted,
        ]
    )
    await db_session.flush()

    await db_session.commit()

    changes = await index_repository(
        session=db_session,
        repository=repository,
        repository_path=tmp_path,
    )

    changes_by_path = {change.path: change.change_type.value for change in changes}

    assert changes_by_path == {
        "src/changed.py": "changed",
        "src/deleted.py": "deleted",
        "src/new.py": "new",
        "src/unchanged.py": "unchanged",
    }

    result = await db_session.execute(
        select(RepositoryFile)
        .where(RepositoryFile.repository_id == repository.id)
        .order_by(RepositoryFile.path)
    )
    indexed_files = {file.path: file for file in result.scalars()}

    assert set(indexed_files) == {
        "src/changed.py",
        "src/new.py",
        "src/unchanged.py",
    }

    assert indexed_files["src/new.py"].content_hash == calculate_file_hash(new_file)
    assert indexed_files["src/new.py"].size_bytes == new_file.stat().st_size

    assert indexed_files["src/changed.py"].content_hash == calculate_file_hash(changed_file)
    assert indexed_files["src/changed.py"].size_bytes == changed_file.stat().st_size

    assert indexed_files["src/unchanged.py"].content_hash == unchanged_hash
    assert indexed_files["src/unchanged.py"].size_bytes == 1

    assert "src/deleted.py" not in indexed_files
