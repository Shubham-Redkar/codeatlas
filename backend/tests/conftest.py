from collections.abc import AsyncGenerator

import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import NullPool

from app.config import get_settings


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession]:
    """
    Provide a database session isolated by an outer transaction.
    """
    settings = get_settings()

    test_engine = create_async_engine(
        settings.database_url,
        poolclass=NullPool,
    )

    async with test_engine.connect() as connection:
        transaction = await connection.begin()

        session = AsyncSession(
            bind=connection,
            expire_on_commit=False,
            join_transaction_mode="create_savepoint",
        )

        try:
            yield session
        finally:
            await session.close()
            await transaction.rollback()

    await test_engine.dispose()
