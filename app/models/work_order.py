from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.sql import func

from app.database import Base


class WorkOrder(Base):
    __tablename__ = "work_orders"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    maintenance_request_id = Column(
        Integer,
        ForeignKey("maintenance_requests.id"),
        nullable=False,
        index=True,
    )

    assigned_to = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=True,
        index=True,
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

    status = Column(
        String(30),
        nullable=False,
        default="Pending",
        index=True,
    )

    scheduled_date = Column(
        DateTime,
        nullable=True,
    )

    completed_at = Column(
        DateTime,
        nullable=True,
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