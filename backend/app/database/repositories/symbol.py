from uuid import UUID

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from ...parser import Symbol as ParsedSymbol
from ..models import Symbol


async def replace_symbols(
    session: AsyncSession,
    repository_file_id: UUID,
    symbols: list[ParsedSymbol],
) -> list[Symbol]:
    """Replace all persisted symbols for a file with newly parsed symbols."""
    await session.execute(
        delete(Symbol).where(
            Symbol.repository_file_id == repository_file_id,
        )
    )

    symbol_records = [
        Symbol(
            repository_file_id=repository_file_id,
            name=symbol.name,
            kind=symbol.kind.value,
            start_byte=symbol.start_byte,
            end_byte=symbol.end_byte,
            start_line=symbol.start_line,
            end_line=symbol.end_line,
            parameters=list(symbol.parameters),
            return_type=symbol.return_type,
            bases=list(symbol.bases),
            parent_name=symbol.parent_name,
        )
        for symbol in symbols
    ]

    session.add_all(symbol_records)
    await session.flush()

    return symbol_records
