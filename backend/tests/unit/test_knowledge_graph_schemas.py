"""Unit tests for Knowledge Graph Pydantic v2 response schemas."""

from uuid import uuid4
import pytest

from app.application.knowledge_graph.get.get_knowledge_graph_use_case import KnowledgeGraphQueryResult
from app.domain.entities.graph_entity import GraphEntity
from app.domain.entities.graph_relationship import GraphRelationship
from app.domain.value_objects.entity_type import EntityType
from app.domain.value_objects.graph_provenance import GraphProvenance
from app.domain.value_objects.relationship_type import RelationshipType
from app.presentation.schemas.graph_response import (
    GraphEdgeResponse,
    GraphNodeResponse,
    GraphProvenanceResponse,
    KnowledgeGraphResponse,
)


def test_graph_provenance_response_serialization() -> None:
    """Verifies GraphProvenance converts cleanly to presentation schema."""
    artifact_id = uuid4()
    extraction_id = uuid4()
    prov = GraphProvenance(
        artifact_id=artifact_id,
        extraction_id=extraction_id,
        confidence="HIGH",
        evidence_snippet="Python developer with 5 years experience",
        source_location="Page 1, Section 2",
        extraction_method="LLM_EXTRACTION",
        metadata={"model": "gemini"},
    )

    resp = GraphProvenanceResponse.from_domain(prov)
    assert resp.artifact_id == artifact_id
    assert resp.extraction_id == extraction_id
    assert resp.confidence == "HIGH"
    assert resp.evidence_snippet == "Python developer with 5 years experience"
    assert resp.source_location == "Page 1, Section 2"
    assert resp.extraction_method == "LLM_EXTRACTION"
    assert resp.metadata == {"model": "gemini"}


def test_graph_node_response_serialization_with_provenance() -> None:
    """Verifies GraphNodeResponse serializes entity and converts EntityType enum to primitive string."""
    user_id = uuid4()
    prov = GraphProvenance(artifact_id=uuid4(), confidence="MEDIUM")
    entity = GraphEntity(
        user_id=user_id,
        entity_type=EntityType.SKILL,
        name="TypeScript",
        properties={"category": "programming"},
    )

    resp = GraphNodeResponse.from_domain(entity, provenance=[prov])
    assert resp.id == entity.id
    assert resp.user_id == user_id
    assert resp.entity_type == "SKILL"
    assert resp.name == "TypeScript"
    assert resp.canonical_name == "typescript"
    assert resp.properties == {"category": "programming"}
    assert len(resp.provenance) == 1
    assert resp.provenance[0].artifact_id == prov.artifact_id


def test_graph_edge_response_serialization_with_provenance() -> None:
    """Verifies GraphEdgeResponse serializes relationship and converts RelationshipType to primitive string."""
    user_id = uuid4()
    src_id = uuid4()
    tgt_id = uuid4()
    prov = GraphProvenance(artifact_id=uuid4(), confidence="HIGH")
    rel = GraphRelationship(
        user_id=user_id,
        source_entity_id=src_id,
        target_entity_id=tgt_id,
        relationship_type=RelationshipType.USES,
        weight=2.5,
        properties={"context": "production"},
    )

    resp = GraphEdgeResponse.from_domain(rel, provenance=[prov])
    assert resp.id == rel.id
    assert resp.user_id == user_id
    assert resp.source_entity_id == src_id
    assert resp.target_entity_id == tgt_id
    assert resp.relationship_type == "USES"
    assert resp.weight == 2.5
    assert resp.properties == {"context": "production"}
    assert len(resp.provenance) == 1


def test_knowledge_graph_response_from_query_result() -> None:
    """Verifies KnowledgeGraphResponse transforms KnowledgeGraphQueryResult into response payload."""
    user_id = uuid4()
    e1 = GraphEntity(user_id=user_id, entity_type=EntityType.SKILL, name="Docker")
    e2 = GraphEntity(user_id=user_id, entity_type=EntityType.PROJECT, name="CloudApp")
    r1 = GraphRelationship(
        user_id=user_id,
        source_entity_id=e2.id,
        target_entity_id=e1.id,
        relationship_type=RelationshipType.USES,
    )

    prov_e1 = GraphProvenance(artifact_id=uuid4(), confidence="HIGH")
    prov_r1 = GraphProvenance(artifact_id=uuid4(), confidence="LOW")

    query_result = KnowledgeGraphQueryResult(
        entities=[e1, e2],
        relationships=[r1],
        entity_provenance={e1.id: [prov_e1]},
        relationship_provenance={r1.id: [prov_r1]},
    )

    resp = KnowledgeGraphResponse.from_query_result(query_result)
    assert resp.total_nodes == 2
    assert resp.total_edges == 1
    assert len(resp.nodes) == 2
    assert len(resp.edges) == 1

    node_docker = next(n for n in resp.nodes if n.name == "Docker")
    assert len(node_docker.provenance) == 1
    assert node_docker.provenance[0].artifact_id == prov_e1.artifact_id

    node_cloudapp = next(n for n in resp.nodes if n.name == "CloudApp")
    assert len(node_cloudapp.provenance) == 0

    assert resp.edges[0].relationship_type == "USES"
    assert len(resp.edges[0].provenance) == 1
    assert resp.edges[0].provenance[0].artifact_id == prov_r1.artifact_id
