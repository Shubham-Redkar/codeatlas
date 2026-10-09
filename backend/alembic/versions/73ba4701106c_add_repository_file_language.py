"""add repository file language

Revision ID: 73ba4701106c
Revises: 060235032339
Create Date: 2026-10-08 19:27:04.706046

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "73ba4701106c"
down_revision: str | Sequence[str] | None = "060235032339"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add the language column and populate existing repository files."""
    op.add_column(
        "repository_files",
        sa.Column(
            "language",
            sa.String(length=32),
            nullable=True,
        ),
    )

    connection = op.get_bind()

    connection.execute(
        sa.text(
            """
            UPDATE repository_files
            SET language = 'python'
            WHERE LOWER(path) LIKE '%.py'
               OR LOWER(path) LIKE '%.pyi'
            """
        )
    )

    connection.execute(
        sa.text(
            """
            UPDATE repository_files
            SET language = 'javascript'
            WHERE LOWER(path) LIKE '%.js'
               OR LOWER(path) LIKE '%.jsx'
               OR LOWER(path) LIKE '%.mjs'
               OR LOWER(path) LIKE '%.cjs'
            """
        )
    )

    connection.execute(
        sa.text(
            """
            UPDATE repository_files
            SET language = 'typescript'
            WHERE LOWER(path) LIKE '%.ts'
               OR LOWER(path) LIKE '%.tsx'
            """
        )
    )


def downgrade() -> None:
    """Remove the language column from repository files."""
    op.drop_column("repository_files", "language")
