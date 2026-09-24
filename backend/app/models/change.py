"""Change Twin model for tracking proposed code changes and graph impact analyses."""

import uuid
from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import GUID, BaseModel

if TYPE_CHECKING:
    from app.models.repository import Repository


class ChangeRecord(BaseModel):
    """Represents a proposed change (Git diff / PR) and its calculated impact on the Reality Graph."""

    __tablename__ = "change_records"

    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    branch: Mapped[str | None] = mapped_column(String(100), nullable=True)
    author: Mapped[str | None] = mapped_column(String(100), nullable=True)
    git_diff: Mapped[str] = mapped_column(Text, nullable=False)

    direct_impact_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    indirect_impact_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    risk_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    risk_level: Mapped[str] = mapped_column(String(50), default="low", nullable=False)  # critical, high, medium, low
    impact_summary: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)

    repository_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(),
        ForeignKey("repositories.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    repository: Mapped["Repository | None"] = relationship("Repository")

    def __repr__(self) -> str:
        return f"<ChangeRecord {self.title} [Risk: {self.risk_level}]>"
