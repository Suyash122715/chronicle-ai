"""SQLAlchemy 2 ORM model for the graph_entities table."""

from datetime import datetime, timezone
from typing import Any
import uuid

from sqlalchemy import DateTime, ForeignKey, String, JSON, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.entities.graph_entity import GraphEntity
from app.domain.value_objects.entity_type import EntityType
from app.infrastructure.db.base import Base


class GraphEntityModel(Base):
    """SQLAlchemy ORM model mapping to the 'graph_entities' PostgreSQL table."""

    __tablename__ = "graph_entities"
    __table_args__ = (
        UniqueConstraint("user_id", "entity_type", "canonical_name", name="uq_graph_entities_user_type_canonical"),
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
    entity_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    canonical_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
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

    def to_domain(self) -> GraphEntity:
        """Converts ORM model to pure Domain GraphEntity entity."""
        return GraphEntity(
            id=self.id,
            user_id=self.user_id,
            entity_type=EntityType.from_string(self.entity_type),
            name=self.name,
            canonical_name=self.canonical_name,
            properties=self.properties or {},
            created_at=self.created_at,
            updated_at=self.updated_at,
        )

    @classmethod
    def from_domain(cls, entity: GraphEntity) -> "GraphEntityModel":
        """Converts Domain GraphEntity entity to ORM model."""
        entity_type_str = (
            entity.entity_type.value
            if isinstance(entity.entity_type, EntityType)
            else str(entity.entity_type)
        )
        return cls(
            id=entity.id,
            user_id=entity.user_id,
            entity_type=entity_type_str,
            name=entity.name,
            canonical_name=entity.canonical_name,
            properties=entity.properties or {},
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )
