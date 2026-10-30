from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PDUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .repository_file import RepositoryFile


class FileDependency(Base):
    """A directed dependency between two repository files."""

    __tablename__ = "file_dependencies"

    __table_args__ = (
        UniqueConstraint(
            "source_file_id",
            "target_file_id",
            name="uq_file_dependency_source_target",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        PDUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    source_file_id: Mapped[UUID] = mapped_column(
        PDUUID(as_uuid=True),
        ForeignKey("repository_files.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    target_file_id: Mapped[UUID] = mapped_column(
        PDUUID(as_uuid=True),
        ForeignKey("repository_files.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    source_file: Mapped["RepositoryFile"] = relationship(
        back_populates="outgoing_dependencies",
        foreign_keys=[source_file_id],
    )

    target_file: Mapped["RepositoryFile"] = relationship(
        back_populates="incoming_dependencies",
        foreign_keys=[target_file_id],
    )
