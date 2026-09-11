"""GraphEntity domain entity representation."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from app.domain.exceptions.base import DomainValidationError
from app.domain.value_objects.entity_type import EntityType


def canonicalize_name(name: str) -> str:
    """Transforms a raw entity name into a normalized canonical name for deduplication.

    Trims whitespace and converts to lowercase.
    Example: '  React.js  ' -> 'react.js'.
    """
    if not name or not isinstance(name, str):
        return ""
    return name.strip().lower()


@dataclass
class GraphEntity:
    """Pure domain entity representing a node in the Knowledge Graph.

    Contains zero framework or ORM dependencies.
    """

    user_id: UUID
    entity_type: EntityType
    name: str
    canonical_name: str = ""
    properties: dict[str, Any] = field(default_factory=dict)
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        if not isinstance(self.user_id, UUID):
            raise DomainValidationError("user_id must be a valid UUID.")
        if not isinstance(self.id, UUID):
            raise DomainValidationError("id must be a valid UUID.")
        if not self.name or not isinstance(self.name, str) or not self.name.strip():
            raise DomainValidationError("Entity name cannot be empty.")

        if not isinstance(self.entity_type, EntityType):
            if isinstance(self.entity_type, str):
                self.entity_type = EntityType.from_string(self.entity_type)
            else:
                raise DomainValidationError("Invalid entity_type.")

        self.name = self.name.strip()
        if not self.canonical_name or not self.canonical_name.strip():
            self.canonical_name = canonicalize_name(self.name)
        else:
            self.canonical_name = canonicalize_name(self.canonical_name)

        if not self.canonical_name:
            raise DomainValidationError("Canonical name cannot be empty.")
