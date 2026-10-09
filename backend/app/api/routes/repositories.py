from fastapi import APIRouter, status
from pydantic import HttpUrl

from ...schemas.repositories import (
    RepositoryCreateRequest,
    RepositoryResponse,
)
from ...services.repositories import ingest_repository
from ..dependencies import SessionDep

router = APIRouter(
    prefix="/repositories",
    tags=["repositories"],
)


@router.post(
    "",
    response_model=RepositoryResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_repository(
    request: RepositoryCreateRequest,
    session: SessionDep,
) -> RepositoryResponse:
    """Create and index a Git repository."""
    repository, file_count = await ingest_repository(
        session=session,
        url=str(request.url),
        branch=request.branch,
    )

    return RepositoryResponse(
        id=repository.id,
        name=repository.name,
        url=HttpUrl(repository.url),
        branch=repository.branch,
        file_count=file_count,
    )
