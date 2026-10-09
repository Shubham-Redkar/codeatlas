from typing import Annotated, get_args, get_origin

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import SessionDep
from app.database.session import get_db


def test_session_dep_is_annotated():
    assert get_origin(SessionDep) is Annotated


def test_session_dep_uses_async_session():
    args = get_args(SessionDep)

    assert args[0] is AsyncSession


def test_session_dep_uses_get_db():
    args = get_args(SessionDep)
    dependency = args[1]

    assert dependency.dependency is get_db
