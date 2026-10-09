from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class RepositoryCreateRequest(BaseModel):
    """Request schema for creating a repository."""

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        json_schema_extra={
            "examples": [
                {
                    "url": "https://github.com/owner/my-project",
                    "branch": "main",
                }
            ]
        },
    )

    url: HttpUrl = Field(
        description="URL of the Git repository.",
        examples=["https://github.com/owner/repository"],
    )

    branch: str | None = Field(
        default=None,
        min_length=1,
        description=(
            "Git branch to use for the repository. "
            "If omitted, the repository's default branch is used."
        ),
        examples=["main"],
    )


class RepositoryResponse(BaseModel):
    """Response schema representing a repository."""

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        json_schema_extra={
            "examples": [
                {
                    "id": "550e8400-e29b-41d4-a716-446655440000",
                    "name": "my-project",
                    "url": "https://github.com/owner/my-project",
                    "branch": "main",
                    "file_count": 128,
                }
            ]
        },
    )

    id: UUID = Field(
        description="Unique identifier of the repository.",
        examples=["550e8400-e29b-41d4-a716-446655440000"],
    )

    name: str = Field(
        min_length=1,
        description="Repository name.",
        examples=["my-project"],
    )

    url: HttpUrl = Field(
        description="URL of the Git repository.",
        examples=["https://github.com/owner/my-project"],
    )

    branch: str = Field(
        min_length=1,
        description="Git branch associated with the repository.",
        examples=["main"],
    )

    file_count: int = Field(
        ge=0,
        description="Number of files indexed in the repository.",
        examples=[128],
    )
