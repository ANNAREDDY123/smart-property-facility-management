from sqlalchemy import Column, Integer, String

from app.database import Base


class Tenant(Base):
    __tablename__ = "tenants"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    full_name = Column(
        String(150),
        nullable=False,
        index=True,
    )

    email = Column(
        String(150),
        nullable=False,
        unique=True,
        index=True,
    )

    phone = Column(
        String(20),
        nullable=False,
    )

    identification_number = Column(
        String(100),
        nullable=False,
        unique=True,
        index=True,
    )

    emergency_contact = Column(
        String(150),
        nullable=False,
    )

    address = Column(
        String(255),
        nullable=False,
    )