"""Base class and schemas for context discrepancy detectors."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class DiscrepancyResult:
    """Standardized result produced by a discrepancy detector."""

    title: str
    finding_type: str
    severity: str  # critical, high, medium, low, info
    confidence: float
    description: str
    file_path: str | None = None
    line_number: int | None = None
    code_snippet: str | None = None
    expected: Any = None
    actual: Any = None
    related_node_ids: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_evidence_payload(self) -> dict[str, Any]:
        """Convert into structured JSON evidence payload for Finding model."""
        return {
            "file_path": self.file_path,
            "line_number": self.line_number,
            "code_snippet": self.code_snippet,
            "expected": self.expected,
            "actual": self.actual,
            "related_node_ids": self.related_node_ids,
            **self.metadata,
        }


class BaseDetector(ABC):
    """Abstract base class for all architectural discrepancy detectors."""

    detector_type: str = "base"

    @abstractmethod
    def detect(
        self,
        nodes: list[dict[str, Any]],
        edges: list[dict[str, Any]],
        file_tree: dict[str, str] | None = None,
    ) -> list[DiscrepancyResult]:
        """Execute detector logic against graph nodes, edges, and optional file contents."""
