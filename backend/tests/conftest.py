from collections.abc import AsyncGenerator

import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import async_session_maker


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession]:
    """
    Provide a database session wrapped in a rollback transaction.
    """
    async with async_session_maker() as session:
        await session.begin()

        try:
            yield session
        finally:
            await session.rollback()
