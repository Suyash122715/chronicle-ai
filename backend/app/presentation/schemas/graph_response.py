"""Knowledge Graph response schemas using Pydantic v2.

Domain value objects and entities are converted to presentation DTOs.
ORM models and internal domain types do not leak into the API layer.
"""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.application.knowledge_graph.get.get_knowledge_graph_use_case import KnowledgeGraphQueryResult
from app.domain.entities.graph_entity import GraphEntity
from app.domain.entities.graph_relationship import GraphRelationship
from app.domain.value_objects.graph_provenance import GraphProvenance


class GraphProvenanceResponse(BaseModel):
    """Provenance citation linking an entity or relationship to its source artifact."""

    model_config = ConfigDict(from_attributes=False)

    artifact_id: UUID
    extraction_id: UUID | None = None
    confidence: str
    evidence_snippet: str | None = None
    source_location: str | None = None
    extraction_method: str = "LLM_EXTRACTION"
    metadata: dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def from_domain(cls, prov: GraphProvenance) -> "GraphProvenanceResponse":
        """Builds schema from GraphProvenance domain value object."""
        confidence_str = (
            prov.confidence.value if hasattr(prov.confidence, "value") else str(prov.confidence)
        )
        return cls(
            artifact_id=prov.artifact_id,
            extraction_id=prov.extraction_id,
            confidence=confidence_str,
            evidence_snippet=prov.evidence_snippet,
            source_location=prov.source_location,
            extraction_method=prov.extraction_method,
            metadata=prov.metadata or {},
        )


class GraphNodeResponse(BaseModel):
    """Response payload schema for a Knowledge Graph entity node."""

    model_config = ConfigDict(from_attributes=False)

    id: UUID
    user_id: UUID
    entity_type: str
    name: str
    canonical_name: str
    properties: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime
    provenance: list[GraphProvenanceResponse] = Field(default_factory=list)

    @classmethod
    def from_domain(
        cls, entity: GraphEntity, provenance: list[GraphProvenance] | None = None
    ) -> "GraphNodeResponse":
        """Builds schema from GraphEntity domain entity and optional provenance list."""
        entity_type_str = (
            entity.entity_type.value if hasattr(entity.entity_type, "value") else str(entity.entity_type)
        )
        prov_list = [GraphProvenanceResponse.from_domain(p) for p in (provenance or [])]
        return cls(
            id=entity.id,
            user_id=entity.user_id,
            entity_type=entity_type_str,
            name=entity.name,
            canonical_name=entity.canonical_name,
            properties=entity.properties or {},
            created_at=entity.created_at,
            updated_at=entity.updated_at,
            provenance=prov_list,
        )


class GraphEdgeResponse(BaseModel):
    """Response payload schema for a directed Knowledge Graph relationship edge."""

    model_config = ConfigDict(from_attributes=False)

    id: UUID
    user_id: UUID
    source_entity_id: UUID
    target_entity_id: UUID
    relationship_type: str
    weight: float = 1.0
    properties: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime
    provenance: list[GraphProvenanceResponse] = Field(default_factory=list)

    @classmethod
    def from_domain(
        cls, relationship: GraphRelationship, provenance: list[GraphProvenance] | None = None
    ) -> "GraphEdgeResponse":
        """Builds schema from GraphRelationship domain entity and optional provenance list."""
        rel_type_str = (
            relationship.relationship_type.value
            if hasattr(relationship.relationship_type, "value")
            else str(relationship.relationship_type)
        )
        prov_list = [GraphProvenanceResponse.from_domain(p) for p in (provenance or [])]
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
            provenance=prov_list,
        )


class KnowledgeGraphResponse(BaseModel):
    """Full knowledge graph response containing nodes, edges, and counts."""

    model_config = ConfigDict(from_attributes=False)

    nodes: list[GraphNodeResponse]
    edges: list[GraphEdgeResponse]
    total_nodes: int
    total_edges: int

    @classmethod
    def from_query_result(cls, result: KnowledgeGraphQueryResult) -> "KnowledgeGraphResponse":
        """Builds KnowledgeGraphResponse from a KnowledgeGraphQueryResult."""
        nodes = [
            GraphNodeResponse.from_domain(
                entity=e,
                provenance=result.entity_provenance.get(e.id, []),
            )
            for e in result.entities
        ]
        edges = [
            GraphEdgeResponse.from_domain(
                relationship=r,
                provenance=result.relationship_provenance.get(r.id, []),
            )
            for r in result.relationships
        ]
        return cls(
            nodes=nodes,
            edges=edges,
            total_nodes=len(nodes),
            total_edges=len(edges),
        )
