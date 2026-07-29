"""Artifact response schemas using Pydantic v2."""

from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict

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
    error_message: str | None = None
    retry_count: int = 0
    created_at: datetime
    updated_at: datetime


class UploadArtifactResponse(BaseModel):
    """Response payload for successful artifact upload."""

    artifact: ArtifactResponse
    message: str = "Artifact uploaded successfully."
