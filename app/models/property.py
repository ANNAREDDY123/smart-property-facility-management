from sqlalchemy import Boolean, Column, Float, Integer, String

from app.database import Base


class Property(Base):
    __tablename__ = "properties"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    property_name = Column(
        String(150),
        nullable=False,
        index=True,
    )

    property_type = Column(
        String(30),
        nullable=False,
        index=True,
    )

    address = Column(
        String(255),
        nullable=False,
    )

    city = Column(
        String(100),
        nullable=False,
        index=True,
    )

    state = Column(
        String(100),
        nullable=False,
    )

    total_area = Column(
        Float,
        nullable=False,
    )

    total_units = Column(
        Integer,
        nullable=False,
    )

    status = Column(
        String(30),
        nullable=False,
        default="Active",
        index=True,
    )

    is_deleted = Column(
        Boolean,
        nullable=False,
        default=False,
        index=True,
    )