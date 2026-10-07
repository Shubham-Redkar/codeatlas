from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


from .repository import Repository

__all__ = [
    "Base",
    "Repository",
]
