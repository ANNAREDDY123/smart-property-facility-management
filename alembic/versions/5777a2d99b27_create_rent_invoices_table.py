"""create rent invoices table

Revision ID: 5777a2d99b27
Revises: 7280a2f3fd41
Create Date: 2026-08-25 16:38:40.621549

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "5777a2d99b27"
down_revision: Union[str, Sequence[str], None] = "7280a2f3fd41"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create rent_invoices table."""

    op.create_table(
        "rent_invoices",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("lease_id", sa.Integer(), nullable=False),
        sa.Column("billing_month", sa.String(length=7), nullable=False),
        sa.Column("rent_amount", sa.Float(), nullable=False),
        sa.Column("late_fee", sa.Float(), nullable=False),
        sa.Column("discount", sa.Float(), nullable=False),
        sa.Column("total_amount", sa.Float(), nullable=False),
        sa.Column("due_date", sa.Date(), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.ForeignKeyConstraint(
            ["lease_id"],
            ["leases.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        op.f("ix_rent_invoices_billing_month"),
        "rent_invoices",
        ["billing_month"],
        unique=False,
    )

    op.create_index(
        op.f("ix_rent_invoices_id"),
        "rent_invoices",
        ["id"],
        unique=False,
    )

    op.create_index(
        op.f("ix_rent_invoices_lease_id"),
        "rent_invoices",
        ["lease_id"],
        unique=False,
    )

    op.create_index(
        op.f("ix_rent_invoices_status"),
        "rent_invoices",
        ["status"],
        unique=False,
    )


def downgrade() -> None:
    """Drop rent_invoices table."""

    op.drop_index(
        op.f("ix_rent_invoices_status"),
        table_name="rent_invoices",
    )

    op.drop_index(
        op.f("ix_rent_invoices_lease_id"),
        table_name="rent_invoices",
    )

    op.drop_index(
        op.f("ix_rent_invoices_id"),
        table_name="rent_invoices",
    )

    op.drop_index(
        op.f("ix_rent_invoices_billing_month"),
        table_name="rent_invoices",
    )

    op.drop_table("rent_invoices")