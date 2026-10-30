from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from ...schemas.dependency_graph import FileDependencyResponse
from ...services import get_file_dependency_details
from ..dependencies import SessionDep

router = APIRouter(
    prefix="/repositories/files",
    tags=["dependency graph"],
)


@router.get(
    "/{file_id}/dependencies",
    response_model=FileDependencyResponse,
    status_code=status.HTTP_200_OK,
)
async def get_file_dependencies(
    file_id: UUID,
    session: SessionDep,
) -> FileDependencyResponse:
    """Return direct and transitive dependencies and dependents for a file."""
    details = await get_file_dependency_details(
        session=session,
        repository_file_id=file_id,
    )

    if details is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Repository file not found.",
        )

    file = details["file"]

    return FileDependencyResponse(
        file_id=file.id,
        path=file.path,
        dependencies=[item.path for item in details["dependencies"]],
        transitive_dependencies=[item.path for item in details["transitive_dependencies"]],
        dependents=[item.path for item in details["dependents"]],
        transitive_dependents=[item.path for item in details["transitive_dependents"]],
    )
