"""Finding model."""

import uuid
from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import GUID, BaseModel

if TYPE_CHECKING:
    from app.models.repository import Repository
    from app.models.service import Service


class Finding(BaseModel):
    """Finding entity representing an analytical conclusion or drift observation."""

    __tablename__ = "findings"

    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    finding_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    severity: Mapped[str] = mapped_column(String(50), default="medium", nullable=False, index=True)
    confidence: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_payload: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="open", nullable=False, index=True)

    repository_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(),
        ForeignKey("repositories.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    service_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(),
        ForeignKey("services.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Relationships
    repository: Mapped["Repository | None"] = relationship("Repository", back_populates="findings")
    service: Mapped["Service | None"] = relationship("Service", back_populates="findings")

    def __repr__(self) -> str:
        return f"<Finding [{self.severity}] {self.title}>"
