from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.sql import func

from app.database import Base


class Visitor(Base):
    __tablename__ = "visitors"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    visitor_name = Column(
        String(150),
        nullable=False,
    )

    phone = Column(
        String(30),
        nullable=False,
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

    purpose = Column(
        String(255),
        nullable=False,
    )

    entry_time = Column(
        DateTime,
        nullable=True,
    )

    exit_time = Column(
        DateTime,
        nullable=True,
    )

    visitor_status = Column(
        String(30),
        nullable=False,
        default="Expected",
        index=True,
    )

    created_at = Column(
        DateTime,
        server_default=func.now(),
        nullable=False,
    )