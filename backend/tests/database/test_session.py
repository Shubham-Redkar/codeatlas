from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.database import session as db_session


@pytest.mark.asyncio
async def test_get_db_yields_session():
    mock_session = MagicMock()
    mock_context = MagicMock()
    mock_context.__aenter__ = AsyncMock(return_value=mock_session)
    mock_context.__aexit__ = AsyncMock(return_value=False)

    with patch.object(
        db_session,
        "async_session_maker",
        return_value=mock_context,
    ):
        generator = db_session.get_db()

        yielded_session = await anext(generator)
        assert yielded_session is mock_session

        await generator.aclose()

    mock_context.__aenter__.assert_awaited_once()
    exit_args = mock_context.__aexit__.await_args.args
    assert exit_args[0] is GeneratorExit
    assert isinstance(exit_args[1], GeneratorExit)


@pytest.mark.asyncio
async def test_check_database_executes_select_one():
    mock_session = MagicMock()
    mock_session.execute = AsyncMock()

    mock_context = MagicMock()
    mock_context.__aenter__ = AsyncMock(return_value=mock_session)
    mock_context.__aexit__ = AsyncMock(return_value=False)

    with patch.object(
        db_session,
        "async_session_maker",
        return_value=mock_context,
    ):
        await db_session.check_database()

    mock_session.execute.assert_awaited_once()
    executed_query = mock_session.execute.await_args.args[0]
    assert str(executed_query) == "SELECT 1"

    mock_context.__aenter__.assert_awaited_once()
    mock_context.__aexit__.assert_awaited_once_with(None, None, None)
