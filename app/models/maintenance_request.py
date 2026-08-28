from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.sql import func

from app.database import Base


class MaintenanceRequest(Base):
    __tablename__ = "maintenance_requests"

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

    tenant_id = Column(
        Integer,
        ForeignKey("tenants.id"),
        nullable=True,
        index=True,
    )

    category = Column(
        String(50),
        nullable=False,
        default="General",
    )

    title = Column(
        String(150),
        nullable=False,
    )

    description = Column(
        Text,
        nullable=False,
    )

    priority = Column(
        String(30),
        nullable=False,
        default="Medium",
        index=True,
    )

    assigned_staff = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=True,
        index=True,
    )

    estimated_cost = Column(
        Float,
        nullable=False,
        default=0,
    )

    actual_cost = Column(
        Float,
        nullable=False,
        default=0,
    )

    status = Column(
        String(30),
        nullable=False,
        default="Open",
        index=True,
    )

    created_at = Column(
        DateTime,
        server_default=func.now(),
        nullable=False,
    )

    updated_at = Column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )