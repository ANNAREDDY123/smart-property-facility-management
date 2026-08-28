from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.sql import func

from app.database import Base


class Notification(Base):
    __tablename__ = "notifications"

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

    notification_type = Column(
        String(50),
        nullable=False,
        index=True,
    )

    title = Column(
        String(150),
        nullable=False,
    )

    message = Column(
        Text,
        nullable=False,
    )

    is_read = Column(
        Boolean,
        nullable=False,
        default=False,
    )

    created_at = Column(
        DateTime,
        server_default=func.now(),
        nullable=False,
        index=True,
    )