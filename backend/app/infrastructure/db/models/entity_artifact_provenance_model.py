"""SQLAlchemy 2 ORM model for the entity_artifact_provenance table."""

from datetime import datetime, timezone
from typing import Any
import uuid

from sqlalchemy import DateTime, ForeignKey, String, JSON, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.value_objects.graph_provenance import GraphProvenance
from app.infrastructure.db.base import Base


class EntityArtifactProvenanceModel(Base):
    """SQLAlchemy ORM model mapping to the 'entity_artifact_provenance' PostgreSQL table."""

    __tablename__ = "entity_artifact_provenance"
    __table_args__ = (
        UniqueConstraint("entity_id", "artifact_id", name="uq_entity_provenance_entity_artifact"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    entity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("graph_entities.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    artifact_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("artifacts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    extraction_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("artifact_extractions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    confidence: Mapped[str] = mapped_column(
        String(32),
        default="LOW",
        nullable=False,
    )
    evidence: Mapped[dict[str, Any]] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        default=dict,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    def to_domain(self) -> GraphProvenance:
        """Converts ORM model to GraphProvenance value object."""
        evidence_dict = self.evidence or {}
        return GraphProvenance(
            artifact_id=self.artifact_id,
            extraction_id=self.extraction_id,
            confidence=self.confidence,
            evidence_snippet=evidence_dict.get("evidence_snippet"),
            source_location=evidence_dict.get("source_location"),
            extraction_method=evidence_dict.get("extraction_method", "LLM_EXTRACTION"),
            metadata=evidence_dict.get("metadata", {}),
        )

    @classmethod
    def from_domain(
        cls, provenance: GraphProvenance, entity_id: uuid.UUID, user_id: uuid.UUID
    ) -> "EntityArtifactProvenanceModel":
        """Converts GraphProvenance domain value object to ORM model."""
        evidence_dict = {
            "evidence_snippet": provenance.evidence_snippet,
            "source_location": provenance.source_location,
            "extraction_method": provenance.extraction_method,
            "metadata": provenance.metadata or {},
        }
        return cls(
            user_id=user_id,
            entity_id=entity_id,
            artifact_id=provenance.artifact_id,
            extraction_id=provenance.extraction_id,
            confidence=provenance.confidence,
            evidence=evidence_dict,
        )
