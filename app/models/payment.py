from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.sql import func

from app.database import Base


class Payment(Base):
    __tablename__ = "payments"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    invoice_id = Column(
        Integer,
        ForeignKey("rent_invoices.id"),
        nullable=False,
        index=True,
    )

    amount = Column(
        Float,
        nullable=False,
    )

    payment_method = Column(
        String(50),
        nullable=False,
    )

    payment_status = Column(
        String(30),
        nullable=False,
        default="Success",
        index=True,
    )

    transaction_reference = Column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
    )

    paid_at = Column(
        DateTime,
        server_default=func.now(),
        nullable=False,
    )