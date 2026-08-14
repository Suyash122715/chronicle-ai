"""SQLAlchemy 2 ORM model for the artifact_extractions table."""

from datetime import datetime, timezone
from typing import Any
import uuid

from sqlalchemy import DateTime, ForeignKey, String, JSON
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.value_objects.classification_result import ConfidenceLevel
from app.domain.value_objects.document_type import DocumentType
from app.domain.value_objects.extraction_result import ExtractionResult, ExtractionStatus
from app.domain.value_objects.provenance import Provenance
from app.infrastructure.db.base import Base


class ArtifactExtractionModel(Base):
    """SQLAlchemy ORM model mapping to the 'artifact_extractions' PostgreSQL table."""

    __tablename__ = "artifact_extractions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    artifact_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("artifacts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    document_type: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(
        String(32),
        default=ExtractionStatus.SUCCESS.value,
        nullable=False,
        index=True,
    )
    structured_data: Mapped[dict[str, Any]] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        default=dict,
        nullable=False,
    )
    provenance: Mapped[dict[str, Any]] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        default=dict,
        nullable=False,
    )
    warnings: Mapped[list[str]] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        default=list,
        nullable=False,
    )
    confidence: Mapped[str] = mapped_column(
        String(32),
        default=ConfidenceLevel.LOW.value,
        nullable=False,
    )
    extractor_version: Mapped[str] = mapped_column(
        String(64),
        default="1.0.0",
        nullable=False,
    )
    prompt_version: Mapped[str] = mapped_column(
        String(32),
        default="v1",
        nullable=False,
    )
    llm_metadata: Mapped[dict[str, Any]] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        default=dict,
        nullable=False,
    )
    error_message: Mapped[str | None] = mapped_column(String(512), nullable=True)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    completed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    def to_domain(self) -> ExtractionResult:
        """Converts ORM model to pure Domain ExtractionResult value object."""
        provenance_map: dict[str, Provenance] = {}
        if self.provenance and isinstance(self.provenance, dict):
            for field_name, pdata in self.provenance.items():
                if isinstance(pdata, dict):
                    provenance_map[field_name] = Provenance(
                        artifact_id=self.artifact_id,
                        page_reference=pdata.get("page_reference"),
                        section_reference=pdata.get("section_reference"),
                        evidence_snippet=pdata.get("evidence_snippet"),
                        evidence_location=pdata.get("evidence_location"),
                        confidence=pdata.get("confidence", "low"),
                        extraction_version=pdata.get("extraction_version", "unknown"),
                    )

        return ExtractionResult(
            artifact_id=self.artifact_id,
            document_type=DocumentType.from_str(self.document_type) if self.document_type else DocumentType.unknown(),
            structured_data=self.structured_data or {},
            provenance=provenance_map,
            warnings=self.warnings or [],
            confidence=ConfidenceLevel(self.confidence) if self.confidence in ConfidenceLevel.__members__.values() or any(self.confidence == c.value for c in ConfidenceLevel) else ConfidenceLevel.LOW,
            extractor_version=self.extractor_version or "1.0.0",
            prompt_version=self.prompt_version or "v1",
            llm_metadata=self.llm_metadata or {},
            started_at=self.started_at,
            completed_at=self.completed_at,
            status=ExtractionStatus(self.status) if any(self.status == s.value for s in ExtractionStatus) else ExtractionStatus.SUCCESS,
            error_message=self.error_message,
        )

    @classmethod
    def from_domain(cls, result: ExtractionResult) -> "ArtifactExtractionModel":
        """Converts Domain ExtractionResult value object to ORM model."""
        prov_dict: dict[str, Any] = {}
        if result.provenance:
            for k, v in result.provenance.items():
                if hasattr(v, "to_dict"):
                    prov_dict[k] = v.to_dict()
                elif isinstance(v, dict):
                    prov_dict[k] = v

        doc_type_str = (
            result.document_type.value
            if isinstance(result.document_type, DocumentType)
            else str(result.document_type)
        )
        conf_str = (
            result.confidence.value
            if isinstance(result.confidence, ConfidenceLevel)
            else str(result.confidence)
        )
        status_str = (
            result.status.value
            if isinstance(result.status, ExtractionStatus)
            else str(result.status)
        )

        return cls(
            artifact_id=result.artifact_id,
            document_type=doc_type_str,
            status=status_str,
            structured_data=result.structured_data or {},
            provenance=prov_dict,
            warnings=result.warnings or [],
            confidence=conf_str,
            extractor_version=result.extractor_version,
            prompt_version=result.prompt_version,
            llm_metadata=result.llm_metadata or {},
            error_message=result.error_message,
            started_at=result.started_at,
            completed_at=result.completed_at,
        )
