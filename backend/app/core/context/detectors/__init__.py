"""Context discrepancy detectors."""

from app.core.context.detectors.base import BaseDetector, DiscrepancyResult
from app.core.context.detectors.contradictory_declarations import (
    ContradictoryDeclarationsDetector,
)
from app.core.context.detectors.documentation_drift import DocumentationDriftDetector
from app.core.context.detectors.endpoint_mismatch import EndpointMismatchDetector
from app.core.context.detectors.missing_documentation import (
    MissingDocumentationDetector,
)
from app.core.context.detectors.naming_mismatch import NamingMismatchDetector
from app.core.context.detectors.schema_mismatch import SchemaMismatchDetector
from app.core.context.detectors.stale_references import StaleReferencesDetector

ALL_DETECTORS: list[type[BaseDetector]] = [
    EndpointMismatchDetector,
    NamingMismatchDetector,
    SchemaMismatchDetector,
    DocumentationDriftDetector,
    MissingDocumentationDetector,
    StaleReferencesDetector,
    ContradictoryDeclarationsDetector,
]

__all__ = [
    "ALL_DETECTORS",
    "BaseDetector",
    "ContradictoryDeclarationsDetector",
    "DiscrepancyResult",
    "DocumentationDriftDetector",
    "EndpointMismatchDetector",
    "MissingDocumentationDetector",
    "NamingMismatchDetector",
    "SchemaMismatchDetector",
    "StaleReferencesDetector",
]
