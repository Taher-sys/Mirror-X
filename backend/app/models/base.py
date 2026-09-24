"""Base model with common fields for all SQLAlchemy models."""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, String, TypeDecorator, func
from sqlalchemy.dialects.mysql import CHAR
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class GUID(TypeDecorator):
    """Platform-independent GUID type that stores UUID as CHAR(36) in MySQL and String(36) in SQLite."""

    impl = String(36)
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "mysql":
            return dialect.type_descriptor(CHAR(36))
        else:
            return dialect.type_descriptor(String(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        # Debug print to see if this is being called
        # print(f"GUID.process_bind_param: {value} ({type(value)})")
        return str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        # Debug print to see if this is being called
        # print(f"GUID.process_result_value: {value} ({type(value)})")
        return uuid.UUID(value)


class TimestampMixin:
    """Mixin for created_at and updated_at timestamps."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class UUIDMixin:
    """Mixin for UUID primary key."""

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        primary_key=True,
        default=uuid.uuid4,
    )


class BaseModel(Base, UUIDMixin, TimestampMixin):
    """Base model for all entities with UUID primary key and timestamps."""

    __abstract__ = True

    def to_dict(self) -> dict[str, Any]:
        """Convert model to dictionary."""
        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
        }
