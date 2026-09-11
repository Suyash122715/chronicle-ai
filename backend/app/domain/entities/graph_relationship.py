"""GraphRelationship domain entity representation."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from app.domain.exceptions.base import DomainValidationError
from app.domain.value_objects.relationship_type import RelationshipType


@dataclass
class GraphRelationship:
    """Pure domain entity representing a directed edge in the Knowledge Graph.

    Contains zero framework or ORM dependencies.
    """

    user_id: UUID
    source_entity_id: UUID
    target_entity_id: UUID
    relationship_type: RelationshipType
    weight: float = 1.0
    properties: dict[str, Any] = field(default_factory=dict)
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        if not isinstance(self.user_id, UUID):
            raise DomainValidationError("user_id must be a valid UUID.")
        if not isinstance(self.source_entity_id, UUID):
            raise DomainValidationError("source_entity_id must be a valid UUID.")
        if not isinstance(self.target_entity_id, UUID):
            raise DomainValidationError("target_entity_id must be a valid UUID.")
        if not isinstance(self.id, UUID):
            raise DomainValidationError("id must be a valid UUID.")

        if self.source_entity_id == self.target_entity_id:
            raise DomainValidationError("Self-referential relationships are not permitted.")

        if not isinstance(self.relationship_type, RelationshipType):
            if isinstance(self.relationship_type, str):
                self.relationship_type = RelationshipType.from_string(self.relationship_type)
            else:
                raise DomainValidationError("Invalid relationship_type.")
