"""Reusable provenance model for AI-derived domain values."""

from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class Provenance:
    """Identifies the source and confidence of a derived value."""

    artifact_id: UUID
    page_reference: str | None = None
    section_reference: str | None = None
    evidence_snippet: str | None = None
    evidence_location: str | None = None
    confidence: str = "low"
    extraction_version: str = "unknown"

    def to_dict(self) -> dict[str, str | None]:
        """Serializes provenance for persistence and transport."""
        return {
            "artifact_id": str(self.artifact_id),
            "page_reference": self.page_reference,
            "section_reference": self.section_reference,
            "evidence_snippet": self.evidence_snippet,
            "evidence_location": self.evidence_location,
            "confidence": self.confidence,
            "extraction_version": self.extraction_version,
        }
