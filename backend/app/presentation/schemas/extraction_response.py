"""Extraction response schemas using Pydantic v2.

Domain value objects (ExtractionStatus, ConfidenceLevel, DocumentType) are
converted to primitive strings at the presentation boundary. ORM models and
domain types do not leak into the API layer.
"""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_validator

from app.domain.value_objects.extraction_result import ExtractionResult


class ExtractionResponse(BaseModel):
    """Response payload schema for an artifact extraction result."""

    model_config = ConfigDict(from_attributes=False)

    artifact_id: UUID
    document_type: str
    structured_data: dict[str, Any]
    provenance: dict[str, Any]
    warnings: list[str]
    confidence: str
    status: str
    extractor_version: str
    prompt_version: str
    llm_metadata: dict[str, Any]
    started_at: datetime
    completed_at: datetime
    error_message: str | None = None

    @field_validator("document_type", mode="before")
    @classmethod
    def _coerce_document_type(cls, v: object) -> str:
        """Converts DocumentType value object to a primitive string."""
        if isinstance(v, str):
            return v
        return str(v)

    @field_validator("confidence", mode="before")
    @classmethod
    def _coerce_confidence(cls, v: object) -> str:
        """Converts ConfidenceLevel enum to a primitive string."""
        if isinstance(v, str):
            return v
        return v.value if hasattr(v, "value") else str(v)

    @field_validator("status", mode="before")
    @classmethod
    def _coerce_status(cls, v: object) -> str:
        """Converts ExtractionStatus enum to a primitive string."""
        if isinstance(v, str):
            return v
        return v.value if hasattr(v, "value") else str(v)

    @field_validator("provenance", mode="before")
    @classmethod
    def _coerce_provenance(cls, v: object) -> dict[str, Any]:
        """Serialises Provenance value objects in provenance map to plain dicts."""
        if not isinstance(v, dict):
            return {}
        result: dict[str, Any] = {}
        for key, prov in v.items():
            if hasattr(prov, "to_dict"):
                result[key] = prov.to_dict()
            elif isinstance(prov, dict):
                result[key] = prov
            else:
                result[key] = str(prov)
        return result

    @classmethod
    def from_domain(cls, extraction_result: ExtractionResult) -> "ExtractionResponse":
        """Constructs an ExtractionResponse from a domain ExtractionResult value object.

        This factory is the sole entry point from the domain layer to the
        presentation layer; it keeps mapping logic out of the router.
        """
        return cls(
            artifact_id=extraction_result.artifact_id,
            document_type=extraction_result.document_type,
            structured_data=extraction_result.structured_data,
            provenance=extraction_result.provenance,
            warnings=extraction_result.warnings,
            confidence=extraction_result.confidence,
            status=extraction_result.status,
            extractor_version=extraction_result.extractor_version,
            prompt_version=extraction_result.prompt_version,
            llm_metadata=extraction_result.llm_metadata,
            started_at=extraction_result.started_at,
            completed_at=extraction_result.completed_at,
            error_message=extraction_result.error_message,
        )
