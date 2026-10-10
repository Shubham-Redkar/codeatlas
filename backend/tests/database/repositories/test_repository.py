from uuid import UUID

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import Repository
from app.database.repositories.repository import create_repository


@pytest.mark.asyncio
async def test_create_repository(
    db_session: AsyncSession,
) -> None:
    repository = await create_repository(
        session=db_session,
        name="CodeAtlas",
        url="https://github.com/example/codeatlas.git",
        branch="main",
    )

    assert repository.id is not None
    assert isinstance(repository.id, UUID)
    assert repository.name == "CodeAtlas"
    assert repository.url == "https://github.com/example/codeatlas.git"
    assert repository.branch == "main"

    result = await db_session.execute(
        select(Repository).where(
            Repository.id == repository.id,
        )
    )

    saved_repository = result.scalar_one()

    assert saved_repository.id == repository.id
    assert saved_repository.name == "CodeAtlas"
    assert saved_repository.url == "https://github.com/example/codeatlas.git"
    assert saved_repository.branch == "main"
    assert repository.created_at is not None
    assert repository.updated_at is not None
