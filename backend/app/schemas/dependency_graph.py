from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class FileDependencyResponse(BaseModel):
    """Response schema representing a file's dependency relationships."""

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        json_schema_extra={
            "examples": [
                {
                    "file_id": "550e8400-e29b-41d4-a716-446655440000",
                    "path": "src/main.py",
                    "dependencies": ["src/helpers.py"],
                    "transitive_dependencies": [
                        "src/helpers.py",
                        "src/config.py",
                    ],
                    "dependents": ["src/cli.py"],
                    "transitive_dependents": [
                        "src/cli.py",
                        "src/app.py",
                    ],
                }
            ]
        },
    )

    file_id: UUID = Field(
        description="Unique identifier of the file.",
        examples=["550e8400-e29b-41d4-a716-446655440000"],
    )

    path: str = Field(
        min_length=1,
        description="Repository-relative path of the file.",
        examples=["src/main.py"],
    )

    dependencies: list[str] = Field(
        description="Paths of files directly imported by this file.",
        examples=[["src/helpers.py"]],
    )

    transitive_dependencies: list[str] = Field(
        description="Paths of all direct and indirect dependencies.",
        examples=[["src/helpers.py", "src/config.py"]],
    )

    dependents: list[str] = Field(
        description="Paths of files that directly depend on this file.",
        examples=[["src/cli.py"]],
    )

    transitive_dependents: list[str] = Field(
        description="Paths of all direct and indirect dependents.",
        examples=[["src/cli.py", "src/app.py"]],
    )
