"""add maintenance request fields

Revision ID: 96107c8c84ac
Revises: 07a94ceea869
Create Date: 2026-08-26 12:30:43.066332

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "96107c8c84ac"
down_revision: Union[str, Sequence[str], None] = "07a94ceea869"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    op.add_column(
        "maintenance_requests",
        sa.Column(
            "category",
            sa.String(length=50),
            nullable=False,
            server_default="General",
        ),
    )

    op.add_column(
        "maintenance_requests",
        sa.Column(
            "assigned_staff",
            sa.Integer(),
            nullable=True,
        ),
    )

    op.add_column(
        "maintenance_requests",
        sa.Column(
            "estimated_cost",
            sa.Float(),
            nullable=False,
            server_default="0",
        ),
    )

    op.add_column(
        "maintenance_requests",
        sa.Column(
            "actual_cost",
            sa.Float(),
            nullable=False,
            server_default="0",
        ),
    )

    op.create_index(
        "ix_maintenance_requests_assigned_staff",
        "maintenance_requests",
        ["assigned_staff"],
        unique=False,
    )

    op.create_foreign_key(
        "fk_maintenance_requests_assigned_staff_users",
        "maintenance_requests",
        "users",
        ["assigned_staff"],
        ["id"],
    )

    # Remove database defaults after existing rows
    # have been populated.
    op.alter_column(
        "maintenance_requests",
        "category",
        server_default=None,
    )

    op.alter_column(
        "maintenance_requests",
        "estimated_cost",
        server_default=None,
    )

    op.alter_column(
        "maintenance_requests",
        "actual_cost",
        server_default=None,
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_constraint(
        "fk_maintenance_requests_assigned_staff_users",
        "maintenance_requests",
        type_="foreignkey",
    )

    op.drop_index(
        "ix_maintenance_requests_assigned_staff",
        table_name="maintenance_requests",
    )

    op.drop_column(
        "maintenance_requests",
        "actual_cost",
    )

    op.drop_column(
        "maintenance_requests",
        "estimated_cost",
    )

    op.drop_column(
        "maintenance_requests",
        "assigned_staff",
    )

    op.drop_column(
        "maintenance_requests",
        "category",
    )