from sqlalchemy import Column, ForeignKey, Integer, String
from app.database import Base


class Parking(Base):
    __tablename__ = "parking"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    property_id = Column(
        Integer,
        ForeignKey("properties.id"),
        nullable=False,
        index=True,
    )

    parking_number = Column(
        String(50),
        nullable=False,
        index=True,
    )

    vehicle_number = Column(
        String(30),
        nullable=True,
        unique=True,
        index=True,
    )

    vehicle_type = Column(
        String(30),
        nullable=True,
    )

    tenant_id = Column(
        Integer,
        ForeignKey("tenants.id"),
        nullable=True,
        index=True,
    )

    status = Column(
        String(30),
        nullable=False,
        default="Available",
        index=True,
    )