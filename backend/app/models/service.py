"""Service model."""

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import GUID, BaseModel

if TYPE_CHECKING:
    from app.models.finding import Finding
    from app.models.repository import Repository


class Service(BaseModel):
    """Service entity representing a deployable software service."""

    __tablename__ = "services"

    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    service_type: Mapped[str] = mapped_column(String(50), default="api", nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="healthy", nullable=False)
    runtime: Mapped[str | None] = mapped_column(String(100), nullable=True)
    version: Mapped[str] = mapped_column(String(50), default="v1.0.0", nullable=False)

    repository_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("repositories.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Relationships
    repository: Mapped["Repository"] = relationship("Repository", back_populates="services")
    findings: Mapped[list["Finding"]] = relationship(
        "Finding",
        back_populates="service",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Service {self.name}>"
