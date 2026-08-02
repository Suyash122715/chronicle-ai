"""ClassificationResult domain value object and ConfidenceLevel enumeration."""

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from app.domain.value_objects.document_type import DocumentType
from app.domain.value_objects.provenance import Provenance


class ConfidenceLevel(str, Enum):
    """Deterministic confidence levels for document classification results."""

    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


@dataclass(frozen=True)
class ClassificationResult:
    """Immutable domain value object representing the result of document classification.

    Once instantiated, instances cannot be modified. Re-classification creates a new instance.
    """

    document_type: DocumentType
    confidence_level: ConfidenceLevel
    classifier_version: str
    classified_at: datetime
    provenance: Provenance

    def to_dict(self) -> dict[str, Any]:
        """Serializes classification result for transport and persistence."""
        return {
            "document_type": self.document_type.value,
            "confidence_level": self.confidence_level.value,
            "classifier_version": self.classifier_version,
            "classified_at": self.classified_at.isoformat(),
            "provenance": self.provenance.to_dict(),
        }
