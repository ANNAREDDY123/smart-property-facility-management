"""add soft delete to properties

Revision ID: ed9329ebeb59
Revises: 5430368f07ef
Create Date: 2026-08-28 15:55:10.640624

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ed9329ebeb59'
down_revision: Union[str, Sequence[str], None] = '5430368f07ef'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "properties",
        sa.Column(
            "is_deleted",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )

    op.create_index(
        "ix_properties_is_deleted",
        "properties",
        ["is_deleted"],
        unique=False,
    )

    op.alter_column(
        "properties",
        "is_deleted",
        server_default=None,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_properties_is_deleted",
        table_name="properties",
    )

    op.drop_column(
        "properties",
        "is_deleted",
    )
