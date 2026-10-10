from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID as PDUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .repository_file import RepositoryFile


class Symbol(Base):
    """Database model representing a symbol extracted from a source file."""

    __tablename__ = "symbols"

    id: Mapped[UUID] = mapped_column(
        PDUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    repository_file_id: Mapped[UUID] = mapped_column(
        PDUUID(as_uuid=True),
        ForeignKey("repository_files.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    kind: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
    )

    start_byte: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    end_byte: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    start_line: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    end_line: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    parameters: Mapped[list[str]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
    )

    return_type: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    bases: Mapped[list[str]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
    )

    parent_name: Mapped[str | None] = mapped_column(
        Text,
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

    repository_file: Mapped["RepositoryFile"] = relationship(
        back_populates="symbols",
    )
