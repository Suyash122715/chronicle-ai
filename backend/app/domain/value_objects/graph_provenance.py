"""GraphProvenance domain value object for knowledge graph traceability."""

from dataclasses import dataclass, field
from typing import Any
from uuid import UUID


@dataclass(frozen=True)
class GraphProvenance:
    """Immutable domain value object representing origin traceability of a graph entity or relationship."""

    artifact_id: UUID
    extraction_id: UUID | None = None
    confidence: str = "LOW"
    evidence_snippet: str | None = None
    source_location: str | None = None
    extraction_method: str = "LLM_EXTRACTION"
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.artifact_id, UUID):
            raise ValueError("artifact_id must be a valid UUID.")

    def to_dict(self) -> dict[str, Any]:
        """Serializes graph provenance for persistence and transport."""
        return {
            "artifact_id": str(self.artifact_id),
            "extraction_id": str(self.extraction_id) if self.extraction_id else None,
            "confidence": self.confidence,
            "evidence_snippet": self.evidence_snippet,
            "source_location": self.source_location,
            "extraction_method": self.extraction_method,
            "metadata": self.metadata,
        }
