"""Artifact response schemas using Pydantic v2.

Classification value objects are converted to primitive strings at the
presentation boundary. Domain types do not leak into the API layer.
"""

from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict, field_validator

from app.domain.entities.artifact import ProcessingStatus


class ArtifactResponse(BaseModel):
    """Response payload schema for artifact details."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    filename: str
    stored_filename: str
    file_size: int
    mime_type: str
    status: ProcessingStatus
    raw_text: str | None = None
    document_type: str | None = None
    classification_confidence: str | None = None
    classifier_version: str | None = None
    classified_at: datetime | None = None
    error_message: str | None = None
    retry_count: int = 0
    created_at: datetime
    updated_at: datetime

    @field_validator("document_type", mode="before")
    @classmethod
    def _coerce_document_type(cls, v: object) -> str | None:
        """Converts DocumentType value object to a primitive string.

        DocumentType must not be exposed outside the domain layer.
        DocumentType.__str__ returns the display value (e.g. 'Resume').
        """
        if v is None:
            return None
        if isinstance(v, str):
            return v
        return str(v)

    @field_validator("classification_confidence", mode="before")
    @classmethod
    def _coerce_confidence_level(cls, v: object) -> str | None:
        """Converts ConfidenceLevel enum to a primitive string.

        ConfidenceLevel is a str Enum; .value returns 'HIGH', 'MEDIUM', or 'LOW'.
        """
        if v is None:
            return None
        if isinstance(v, str):
            return v
        return v.value if hasattr(v, "value") else str(v)


class UploadArtifactResponse(BaseModel):
    """Response payload for successful artifact upload."""

    artifact: ArtifactResponse
    message: str = "Artifact uploaded successfully."
