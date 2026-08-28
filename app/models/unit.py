from sqlalchemy import Column, Float, ForeignKey, Integer, String, UniqueConstraint

from app.database import Base


class Unit(Base):
    __tablename__ = "units"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    building_id = Column(
        Integer,
        ForeignKey("buildings.id"),
        nullable=False,
        index=True,
    )

    unit_number = Column(
        String(50),
        nullable=False,
    )

    floor_number = Column(
        Integer,
        nullable=False,
    )

    unit_type = Column(
        String(50),
        nullable=False,
    )

    area = Column(
        Float,
        nullable=False,
    )

    monthly_rent = Column(
        Float,
        nullable=False,
    )

    status = Column(
        String(30),
        nullable=False,
        default="Available",
        index=True,
    )

    __table_args__ = (
        UniqueConstraint(
            "building_id",
            "unit_number",
            name="uq_building_unit_number",
        ),
    )