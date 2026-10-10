from sqlalchemy.ext.asyncio import AsyncSession

from ..models.repository import Repository


async def create_repository(
    session: AsyncSession,
    name: str,
    url: str,
    branch: str,
) -> Repository:
    """
    Create a repository record.
    """
    repository = Repository(
        name=name,
        url=url,
        branch=branch,
    )

    session.add(repository)
    await session.flush()

    return repository
