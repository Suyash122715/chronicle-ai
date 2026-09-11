"""SQLAlchemy 2 ORM model for the graph_relationships table."""

from datetime import datetime, timezone
from typing import Any
import uuid

from sqlalchemy import DateTime, Float, ForeignKey, String, JSON, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.entities.graph_relationship import GraphRelationship
from app.domain.value_objects.relationship_type import RelationshipType
from app.infrastructure.db.base import Base


class GraphRelationshipModel(Base):
    """SQLAlchemy ORM model mapping to the 'graph_relationships' PostgreSQL table."""

    __tablename__ = "graph_relationships"
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "source_entity_id",
            "target_entity_id",
            "relationship_type",
            name="uq_graph_relationships_user_source_target_type",
        ),
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
    source_entity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("graph_entities.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    target_entity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("graph_entities.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    relationship_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    weight: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    properties: Mapped[dict[str, Any]] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        default=dict,
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

    def to_domain(self) -> GraphRelationship:
        """Converts ORM model to pure Domain GraphRelationship entity."""
        return GraphRelationship(
            id=self.id,
            user_id=self.user_id,
            source_entity_id=self.source_entity_id,
            target_entity_id=self.target_entity_id,
            relationship_type=RelationshipType.from_string(self.relationship_type),
            weight=self.weight,
            properties=self.properties or {},
            created_at=self.created_at,
            updated_at=self.updated_at,
        )

    @classmethod
    def from_domain(cls, relationship: GraphRelationship) -> "GraphRelationshipModel":
        """Converts Domain GraphRelationship entity to ORM model."""
        rel_type_str = (
            relationship.relationship_type.value
            if isinstance(relationship.relationship_type, RelationshipType)
            else str(relationship.relationship_type)
        )
        return cls(
            id=relationship.id,
            user_id=relationship.user_id,
            source_entity_id=relationship.source_entity_id,
            target_entity_id=relationship.target_entity_id,
            relationship_type=rel_type_str,
            weight=relationship.weight,
            properties=relationship.properties or {},
            created_at=relationship.created_at,
            updated_at=relationship.updated_at,
        )
