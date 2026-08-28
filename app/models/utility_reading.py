from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.sql import func

from app.database import Base


class UtilityReading(Base):
    __tablename__ = "utility_readings"

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

    previous_reading = Column(
        Float,
        nullable=False,
    )

    current_reading = Column(
        Float,
        nullable=False,
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

    billing_month = Column(
        String(7),
        nullable=False,
        index=True,
    )

    created_at = Column(
        DateTime,
        server_default=func.now(),
        nullable=False,
    )