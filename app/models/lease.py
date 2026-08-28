from sqlalchemy import Column, Date, Float, ForeignKey, Integer, String

from app.database import Base


class Lease(Base):
    __tablename__ = "leases"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    tenant_id = Column(
        Integer,
        ForeignKey("tenants.id"),
        nullable=False,
        index=True,
    )

    unit_id = Column(
        Integer,
        ForeignKey("units.id"),
        nullable=False,
        index=True,
    )

    start_date = Column(
        Date,
        nullable=False,
    )

    end_date = Column(
        Date,
        nullable=False,
    )

    monthly_rent = Column(
        Float,
        nullable=False,
    )

    security_deposit = Column(
        Float,
        nullable=False,
    )

    lease_status = Column(
        String(30),
        nullable=False,
        default="Draft",
        index=True,
    )