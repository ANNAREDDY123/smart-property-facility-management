from sqlalchemy import Column, ForeignKey, Integer, String

from app.database import Base


class Building(Base):
    __tablename__ = "buildings"

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

    building_name = Column(
        String(150),
        nullable=False,
    )

    number_of_floors = Column(
        Integer,
        nullable=False,
    )

    total_units = Column(
        Integer,
        nullable=False,
    )