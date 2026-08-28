from sqlalchemy import Column, Date, Float, ForeignKey, Integer, String

from app.database import Base


class RentInvoice(Base):
    __tablename__ = "rent_invoices"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    lease_id = Column(
        Integer,
        ForeignKey("leases.id"),
        nullable=False,
        index=True,
    )

    billing_month = Column(
        String(7),
        nullable=False,
        index=True,
    )

    rent_amount = Column(
        Float,
        nullable=False,
    )

    late_fee = Column(
        Float,
        nullable=False,
        default=0,
    )

    discount = Column(
        Float,
        nullable=False,
        default=0,
    )

    total_amount = Column(
        Float,
        nullable=False,
    )

    due_date = Column(
        Date,
        nullable=False,
    )

    status = Column(
        String(30),
        nullable=False,
        default="Pending",
        index=True,
    )