"""create utility tables

Revision ID: a1e8aedaac20
Revises: 96107c8c84ac
Create Date: 2026-08-26 12:52:31.335793

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "a1e8aedaac20"
down_revision: Union[str, Sequence[str], None] = "96107c8c84ac"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    op.create_table(
        "utility_readings",

        sa.Column(
            "id",
            sa.Integer(),
            nullable=False,
        ),

        sa.Column(
            "unit_id",
            sa.Integer(),
            nullable=False,
        ),

        sa.Column(
            "utility_type",
            sa.String(length=30),
            nullable=False,
        ),

        sa.Column(
            "previous_reading",
            sa.Float(),
            nullable=False,
        ),

        sa.Column(
            "current_reading",
            sa.Float(),
            nullable=False,
        ),

        sa.Column(
            "units_consumed",
            sa.Float(),
            nullable=False,
        ),

        sa.Column(
            "rate",
            sa.Float(),
            nullable=False,
        ),

        sa.Column(
            "total_amount",
            sa.Float(),
            nullable=False,
        ),

        sa.Column(
            "billing_month",
            sa.String(length=7),
            nullable=False,
        ),

        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("now()"),
            nullable=False,
        ),

        sa.ForeignKeyConstraint(
            ["unit_id"],
            ["units.id"],
        ),

        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        "ix_utility_readings_id",
        "utility_readings",
        ["id"],
        unique=False,
    )

    op.create_index(
        "ix_utility_readings_unit_id",
        "utility_readings",
        ["unit_id"],
        unique=False,
    )

    op.create_index(
        "ix_utility_readings_utility_type",
        "utility_readings",
        ["utility_type"],
        unique=False,
    )

    op.create_index(
        "ix_utility_readings_billing_month",
        "utility_readings",
        ["billing_month"],
        unique=False,
    )

    op.create_table(
        "utility_invoices",

        sa.Column(
            "id",
            sa.Integer(),
            nullable=False,
        ),

        sa.Column(
            "unit_id",
            sa.Integer(),
            nullable=False,
        ),

        sa.Column(
            "utility_type",
            sa.String(length=30),
            nullable=False,
        ),

        sa.Column(
            "billing_month",
            sa.String(length=7),
            nullable=False,
        ),

        sa.Column(
            "units_consumed",
            sa.Float(),
            nullable=False,
        ),

        sa.Column(
            "rate",
            sa.Float(),
            nullable=False,
        ),

        sa.Column(
            "total_amount",
            sa.Float(),
            nullable=False,
        ),

        sa.Column(
            "status",
            sa.String(length=30),
            nullable=False,
            server_default="Pending",
        ),

        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("now()"),
            nullable=False,
        ),

        sa.ForeignKeyConstraint(
            ["unit_id"],
            ["units.id"],
        ),

        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        "ix_utility_invoices_id",
        "utility_invoices",
        ["id"],
        unique=False,
    )

    op.create_index(
        "ix_utility_invoices_unit_id",
        "utility_invoices",
        ["unit_id"],
        unique=False,
    )

    op.create_index(
        "ix_utility_invoices_utility_type",
        "utility_invoices",
        ["utility_type"],
        unique=False,
    )

    op.create_index(
        "ix_utility_invoices_billing_month",
        "utility_invoices",
        ["billing_month"],
        unique=False,
    )

    op.create_index(
        "ix_utility_invoices_status",
        "utility_invoices",
        ["status"],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_index(
        "ix_utility_invoices_status",
        table_name="utility_invoices",
    )

    op.drop_index(
        "ix_utility_invoices_billing_month",
        table_name="utility_invoices",
    )

    op.drop_index(
        "ix_utility_invoices_utility_type",
        table_name="utility_invoices",
    )

    op.drop_index(
        "ix_utility_invoices_unit_id",
        table_name="utility_invoices",
    )

    op.drop_index(
        "ix_utility_invoices_id",
        table_name="utility_invoices",
    )

    op.drop_table("utility_invoices")

    op.drop_index(
        "ix_utility_readings_billing_month",
        table_name="utility_readings",
    )

    op.drop_index(
        "ix_utility_readings_utility_type",
        table_name="utility_readings",
    )

    op.drop_index(
        "ix_utility_readings_unit_id",
        table_name="utility_readings",
    )

    op.drop_index(
        "ix_utility_readings_id",
        table_name="utility_readings",
    )

    op.drop_table("utility_readings")