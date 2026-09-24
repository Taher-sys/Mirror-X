"""Repository model."""

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import GUID, BaseModel

if TYPE_CHECKING:
    from app.models.finding import Finding
    from app.models.project import Project
    from app.models.service import Service


class Repository(BaseModel):
    """Repository entity representing a source code repository."""

    __tablename__ = "repositories"

    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    url: Mapped[str] = mapped_column(String(1024), nullable=False)
    default_branch: Mapped[str] = mapped_column(String(100), default="main", nullable=False)
    language: Mapped[str | None] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="active", nullable=False)

    project_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="repositories")
    services: Mapped[list["Service"]] = relationship(
        "Service",
        back_populates="repository",
        cascade="all, delete-orphan",
    )
    findings: Mapped[list["Finding"]] = relationship(
        "Finding",
        back_populates="repository",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Repository {self.name}>"
