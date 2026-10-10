from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import BigInteger, DateTime, ForeignKey, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID as PDUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .repository import Repository
    from .symbol import Symbol


class RepositoryFile(Base):
    """
    Database model representing a file belonging to a repository.
    """

    __tablename__ = "repository_files"

    __table_args__ = (
        UniqueConstraint(
            "repository_id",
            "path",
            name="uq_repository_file_repository_path",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        PDUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    repository_id: Mapped[UUID] = mapped_column(
        PDUUID(as_uuid=True),
        ForeignKey(
            "repositories.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    path: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    content_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )

    size_bytes: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
    )

    language: Mapped[str | None] = mapped_column(
        String(32),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    repository: Mapped["Repository"] = relationship(
        back_populates="files",
    )

    symbols: Mapped[list["Symbol"]] = relationship(
        back_populates="repository_file",
        cascade="all, delete-orphan",
    )
