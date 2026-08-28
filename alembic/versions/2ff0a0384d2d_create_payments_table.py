"""create payments table

Revision ID: 2ff0a0384d2d
Revises: 5777a2d99b27
Create Date: 2026-08-25 16:57:39.326071

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "2ff0a0384d2d"
down_revision: Union[str, Sequence[str], None] = "5777a2d99b27"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    op.create_table(
        "payments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("invoice_id", sa.Integer(), nullable=False),
        sa.Column("amount", sa.Float(), nullable=False),
        sa.Column(
            "payment_method",
            sa.String(length=50),
            nullable=False,
        ),
        sa.Column(
            "payment_status",
            sa.String(length=30),
            nullable=False,
        ),
        sa.Column(
            "transaction_reference",
            sa.String(length=100),
            nullable=False,
        ),
        sa.Column(
            "paid_at",
            sa.DateTime(),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["invoice_id"],
            ["rent_invoices.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("transaction_reference"),
       
    )

    op.create_index(
        op.f("ix_payments_id"),
        "payments",
        ["id"],
        unique=False,
    )

    op.create_index(
        op.f("ix_payments_invoice_id"),
        "payments",
        ["invoice_id"],
        unique=False,
    )

    op.create_index(
        op.f("ix_payments_payment_status"),
        "payments",
        ["payment_status"],
        unique=False,
    )

    op.create_index(
        op.f("ix_payments_transaction_reference"),
        "payments",
        ["transaction_reference"],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_index(
        op.f("ix_payments_transaction_reference"),
        table_name="payments",
    )

    op.drop_index(
        op.f("ix_payments_payment_status"),
        table_name="payments",
    )

    op.drop_index(
        op.f("ix_payments_invoice_id"),
        table_name="payments",
    )

    op.drop_index(
        op.f("ix_payments_id"),
        table_name="payments",
    )

    op.drop_table("payments")