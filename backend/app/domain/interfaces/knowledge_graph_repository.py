"""Knowledge Graph repository interface definition."""

from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.entities.graph_entity import GraphEntity
from app.domain.entities.graph_relationship import GraphRelationship
from app.domain.value_objects.entity_type import EntityType
from app.domain.value_objects.graph_provenance import GraphProvenance


class KnowledgeGraphRepositoryInterface(ABC):
    """Abstract interface defining persistence operations for Knowledge Graph entities, relationships, and provenance.

    Domain interfaces MUST NOT import SQLAlchemy or other infrastructure/database frameworks.
    """

    @abstractmethod
    async def save_entity(
        self, entity: GraphEntity, provenance: GraphProvenance | None = None
    ) -> GraphEntity:
        """Persists or updates a GraphEntity domain entity and links provenance if provided."""
        pass

    @abstractmethod
    async def get_entity_by_id(self, entity_id: UUID) -> GraphEntity | None:
        """Retrieves a GraphEntity by its unique UUID."""
        pass

    @abstractmethod
    async def get_entity_by_canonical(
        self, user_id: UUID, entity_type: EntityType, canonical_name: str
    ) -> GraphEntity | None:
        """Retrieves a GraphEntity for a specific user matching entity_type and canonical_name."""
        pass

    @abstractmethod
    async def list_entities_by_user(
        self, user_id: UUID, entity_type: EntityType | None = None
    ) -> list[GraphEntity]:
        """Retrieves all GraphEntities owned by the given user, optionally filtered by entity_type."""
        pass

    @abstractmethod
    async def save_relationship(
        self, relationship: GraphRelationship, provenance: GraphProvenance | None = None
    ) -> GraphRelationship:
        """Persists or updates a GraphRelationship domain entity and links provenance if provided."""
        pass

    @abstractmethod
    async def get_relationship_by_id(self, relationship_id: UUID) -> GraphRelationship | None:
        """Retrieves a GraphRelationship by its unique UUID."""
        pass

    @abstractmethod
    async def get_user_graph(
        self, user_id: UUID, artifact_id: UUID | None = None, entity_type: EntityType | None = None
    ) -> tuple[list[GraphEntity], list[GraphRelationship]]:
        """Retrieves the full subgraph of entities and relationships for a user, optionally filtered by artifact or type."""
        pass

    @abstractmethod
    async def delete_entity(self, entity_id: UUID) -> bool:
        """Deletes a graph entity and its associated relationships."""
        pass

    @abstractmethod
    async def delete_provenance_by_artifact_id(self, artifact_id: UUID) -> bool:
        """Deletes graph entity/relationship provenance records associated with an artifact ID."""
        pass

    @abstractmethod
    async def persist_graph(
        self,
        entities: list[GraphEntity],
        relationships: list[GraphRelationship],
        entity_provenance: dict[UUID, GraphProvenance] | None = None,
        relationship_provenance: dict[UUID, GraphProvenance] | None = None,
    ) -> tuple[list[GraphEntity], list[GraphRelationship]]:
        """Atomically persists a collection of entities, relationships, and provenance records.

        Resolves semantic entity identities, remaps foreign keys to database entity IDs,
        and guarantees transactional atomicity.
        """
        pass
