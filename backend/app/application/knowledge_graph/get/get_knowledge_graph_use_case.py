"""Get Knowledge Graph Use Case implementation."""

from dataclasses import dataclass, field
from uuid import UUID

from app.domain.entities.graph_entity import GraphEntity
from app.domain.entities.graph_relationship import GraphRelationship
from app.domain.exceptions.artifact_exceptions import ArtifactNotFoundError
from app.domain.exceptions.base import DomainValidationError
from app.domain.interfaces.artifact_repository import ArtifactRepositoryInterface
from app.domain.interfaces.knowledge_graph_repository import KnowledgeGraphRepositoryInterface
from app.domain.value_objects.entity_type import EntityType
from app.domain.value_objects.graph_provenance import GraphProvenance


@dataclass(frozen=True)
class KnowledgeGraphQueryResult:
    """Domain query result containing nodes, edges, and optional provenance mappings."""

    entities: list[GraphEntity]
    relationships: list[GraphRelationship]
    entity_provenance: dict[UUID, list[GraphProvenance]] = field(default_factory=dict)
    relationship_provenance: dict[UUID, list[GraphProvenance]] = field(default_factory=dict)


class GetKnowledgeGraphUseCase:
    """Application use case for retrieving a user's knowledge graph with optional filtering."""

    def __init__(
        self,
        knowledge_graph_repository: KnowledgeGraphRepositoryInterface,
        artifact_repository: ArtifactRepositoryInterface,
    ) -> None:
        self._kg_repository = knowledge_graph_repository
        self._artifact_repository = artifact_repository

    async def execute(
        self,
        user_id: UUID,
        artifact_id: UUID | None = None,
        entity_type: str | None = None,
        include_provenance: bool = True,
    ) -> KnowledgeGraphQueryResult:
        """Retrieves the knowledge graph for the authenticated user.

        Args:
            user_id: Authenticated user ID enforcing data isolation.
            artifact_id: Optional artifact ID to filter subgraph to elements from that artifact.
            entity_type: Optional entity type string (e.g. 'SKILL', 'COMPANY') to filter nodes.
            include_provenance: If True, fetches provenance records in batch.

        Raises:
            ArtifactNotFoundError: If artifact_id does not exist or belongs to another user.
            DomainValidationError: If entity_type string is invalid.

        Returns:
            KnowledgeGraphQueryResult: Entities, relationships, and provenance maps.
        """
        # 1. Enforce user ownership if artifact_id is supplied
        if artifact_id is not None:
            artifact = await self._artifact_repository.get_by_id(artifact_id)
            if artifact is None or artifact.user_id != user_id:
                raise ArtifactNotFoundError()

        # 2. Validate entity_type if supplied
        parsed_entity_type: EntityType | None = None
        if entity_type is not None and entity_type.strip():
            clean_type = entity_type.strip().upper()
            try:
                parsed_entity_type = EntityType(clean_type)
                if parsed_entity_type == EntityType.UNKNOWN:
                    raise ValueError("UNKNOWN is not a queryable filter type")
            except ValueError:
                allowed_types = [e.value for e in EntityType if e != EntityType.UNKNOWN]
                raise DomainValidationError(
                    f"Invalid entity_type '{entity_type}'. Allowed types: {', '.join(allowed_types)}"
                )

        # 3. Fetch nodes and edges via repository
        entities, relationships = await self._kg_repository.get_user_graph(
            user_id=user_id,
            artifact_id=artifact_id,
            entity_type=parsed_entity_type,
        )

        # 4. Fetch provenance in batch if requested
        entity_prov: dict[UUID, list[GraphProvenance]] = {}
        rel_prov: dict[UUID, list[GraphProvenance]] = {}

        if include_provenance:
            if entities:
                entity_ids = [e.id for e in entities]
                entity_prov = await self._kg_repository.get_provenance_for_entities(
                    user_id=user_id,
                    entity_ids=entity_ids,
                )
            if relationships:
                rel_ids = [r.id for r in relationships]
                rel_prov = await self._kg_repository.get_provenance_for_relationships(
                    user_id=user_id,
                    relationship_ids=rel_ids,
                )

        return KnowledgeGraphQueryResult(
            entities=entities,
            relationships=relationships,
            entity_provenance=entity_prov,
            relationship_provenance=rel_prov,
        )
