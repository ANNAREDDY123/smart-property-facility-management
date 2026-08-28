from sqlalchemy import Column, Date, ForeignKey, Integer, String, Time
from app.database import Base


class FacilityBooking(Base):
    __tablename__ = "facility_bookings"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    facility_id = Column(
        Integer,
        ForeignKey("facilities.id"),
        nullable=False,
        index=True,
    )

    tenant_id = Column(
        Integer,
        ForeignKey("tenants.id"),
        nullable=False,
        index=True,
    )

    booking_date = Column(
        Date,
        nullable=False,
        index=True,
    )

    start_time = Column(
        Time,
        nullable=False,
    )

    end_time = Column(
        Time,
        nullable=False,
    )

    status = Column(
        String(30),
        nullable=False,
        default="Confirmed",
        index=True,
    )