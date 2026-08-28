from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.sql import func

from app.database import Base


class UtilityInvoice(Base):
    __tablename__ = "utility_invoices"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    unit_id = Column(
        Integer,
        ForeignKey("units.id"),
        nullable=False,
        index=True,
    )

    utility_type = Column(
        String(30),
        nullable=False,
        index=True,
    )

    billing_month = Column(
        String(7),
        nullable=False,
        index=True,
    )

    units_consumed = Column(
        Float,
        nullable=False,
    )

    rate = Column(
        Float,
        nullable=False,
    )

    total_amount = Column(
        Float,
        nullable=False,
    )

    status = Column(
        String(30),
        nullable=False,
        default="Pending",
        index=True,
    )

    created_at = Column(
        DateTime,
        server_default=func.now(),
        nullable=False,
    )