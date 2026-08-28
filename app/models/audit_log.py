from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.sql import func

from app.database import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    action = Column(
        String(100),
        nullable=False,
        index=True,
    )

    entity_type = Column(
        String(100),
        nullable=False,
        index=True,
    )

    entity_id = Column(
        Integer,
        nullable=True,
        index=True,
    )

    description = Column(
        Text,
        nullable=False,
    )

    created_at = Column(
        DateTime,
        server_default=func.now(),
        nullable=False,
        index=True,
    )