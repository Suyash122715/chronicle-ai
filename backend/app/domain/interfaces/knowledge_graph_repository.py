"""Knowledge Graph repository interface definition."""

from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.career_intelligence.skill_metric_profile import SkillMetricProfile
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

    @abstractmethod
    async def get_provenance_for_entities(
        self, user_id: UUID, entity_ids: list[UUID]
    ) -> dict[UUID, list[GraphProvenance]]:
        """Retrieves all provenance records for a given list of entity IDs belonging to the user."""
        pass

    @abstractmethod
    async def get_provenance_for_relationships(
        self, user_id: UUID, relationship_ids: list[UUID]
    ) -> dict[UUID, list[GraphProvenance]]:
        """Retrieves all provenance records for a given list of relationship IDs belonging to the user."""
        pass

    @abstractmethod
    async def get_skill_metric_profiles(
        self, user_id: UUID
    ) -> list[SkillMetricProfile]:
        """Aggregates Career Intelligence metric counts for all SKILL and TECHNOLOGY entities owned by the user.

        Metric definitions:
            frequency:        COUNT(DISTINCT artifact_id) from entity_artifact_provenance per entity.
            project_count:    COUNT(DISTINCT source_entity_id) of USES edges where source entity_type == 'PROJECT'.
            experience_count: COUNT(DISTINCT source_entity_id) of USES edges where source entity_type == 'ROLE'.
                              COMPANY nodes are explicitly excluded.
            certificate_count: COUNT(DISTINCT source_entity_id) of CERTIFIED_IN edges where source == 'CERTIFICATE'.
        """
        pass

    @abstractmethod
    async def rebuild_artifact_graph(
        self,
        user_id: UUID,
        artifact_id: UUID,
        fresh_entities: list[GraphEntity],
        fresh_relationships: list[GraphRelationship],
        entity_provenance: dict[UUID, GraphProvenance] | None = None,
        relationship_provenance: dict[UUID, GraphProvenance] | None = None,
    ) -> tuple[list[GraphEntity], list[GraphRelationship]]:
        """Atomically rebuilds the graph contribution of a single artifact.

        Algorithm (8 steps):
        1. Begin transaction savepoint.
        2. Fetch entity_ids and relationship_ids currently supported by artifact_id.
        3. Delete entity_artifact_provenance rows WHERE artifact_id = :artifact_id.
        4. Delete relationship_artifact_provenance rows WHERE artifact_id = :artifact_id.
        5. Delete graph_relationships with zero remaining provenance (orphaned edges).
        6. Delete graph_entities with zero remaining provenance AND zero connected edges (orphaned nodes).
        7. Upsert fresh_entities and fresh_relationships with property reconciliation rules.
        8. Commit / verify.

        Property reconciliation invariants:
            - canonical_name and entity_type are immutable after first insertion.
            - entity properties: earliest-insertion-wins on key collision (existing keys never overwritten).
            - relationship weight: max(existing_weight, incoming_weight).
            - provenance: (entity_id, artifact_id) is idempotent — duplicate upserts are no-ops.

        Rebuild order-independence: calling this method for all artifacts in any order produces
        the same final graph state.
        """
        pass

    @abstractmethod
    async def rebuild_user_graph(
        self,
        user_id: UUID,
    ) -> None:
        """Full user-scoped graph rebuild: replays all valid artifact extractions in ascending
        created_at order to produce an order-independent final graph state.

        This method is called by administrative or correction workflows. It does not delete
        user-scoped entities first; instead it relies on rebuild_artifact_graph() for each
        artifact to prune stale provenance and edges incrementally.
        """
        pass

