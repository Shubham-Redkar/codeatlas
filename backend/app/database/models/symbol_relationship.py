from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PDUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .symbol import Symbol


class SymbolRelationship(Base):
    """A directed relationship between two code symbols."""

    __tablename__ = "symbol_relationships"

    __table_args__ = (
        UniqueConstraint(
            "source_symbol_id",
            "target_symbol_id",
            "kind",
            name="uq_symbol_relationship_source_target_kind",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        PDUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    source_symbol_id: Mapped[UUID] = mapped_column(
        PDUUID(as_uuid=True),
        ForeignKey("symbols.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    target_symbol_id: Mapped[UUID] = mapped_column(
        PDUUID(as_uuid=True),
        ForeignKey("symbols.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    kind: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
    )

    line: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    source_symbol: Mapped["Symbol"] = relationship(
        foreign_keys=[source_symbol_id],
    )

    target_symbol: Mapped["Symbol"] = relationship(
        foreign_keys=[target_symbol_id],
    )
