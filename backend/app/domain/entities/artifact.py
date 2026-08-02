"""Artifact domain entity representation."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
import uuid

from app.domain.value_objects.document_type import DocumentType
from app.domain.value_objects.classification_result import ConfidenceLevel


class ProcessingStatus(str, Enum):
    """Artifact processing pipeline status enumeration."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class Artifact:
    """Pure domain entity representing an uploaded artifact/document.

    Contains zero framework or ORM dependencies.
    """

    user_id: uuid.UUID
    filename: str
    stored_filename: str
    file_path: str
    file_size: int
    mime_type: str
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    status: ProcessingStatus = ProcessingStatus.PENDING
    raw_text: str | None = None
    error_message: str | None = None
    retry_count: int = 0
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    # Classification fields (nullable, backward compatible)
    document_type: DocumentType = field(default_factory=DocumentType.unknown)
    classification_confidence: ConfidenceLevel = field(default_factory=lambda: ConfidenceLevel.LOW)
    classifier_version: str | None = None
    classified_at: datetime | None = None
