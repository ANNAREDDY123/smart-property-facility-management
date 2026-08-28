from sqlalchemy import Column, Integer, String
from app.database import Base


class Facility(Base):
    __tablename__ = "facilities"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    name = Column(
        String(100),
        nullable=False,
        unique=True,
        index=True,
    )

    capacity = Column(
        Integer,
        nullable=False,
    )

    status = Column(
        String(30),
        nullable=False,
        default="Active",
        index=True,
    )