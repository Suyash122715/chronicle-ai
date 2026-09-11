"""Unit tests for Knowledge Graph domain entities, value objects, and interfaces."""

from uuid import uuid4
import pytest

from app.domain.entities.graph_entity import GraphEntity, canonicalize_name
from app.domain.entities.graph_relationship import GraphRelationship
from app.domain.exceptions.base import DomainValidationError
from app.domain.exceptions.graph_exceptions import (
    GraphEntityNotFoundError,
    GraphRelationshipNotFoundError,
)
from app.domain.value_objects.entity_type import EntityType
from app.domain.value_objects.graph_provenance import GraphProvenance
from app.domain.value_objects.relationship_type import RelationshipType


def test_canonicalize_name() -> None:
    """Verifies string canonicalization for deduplication."""
    assert canonicalize_name("  React.js  ") == "react.js"
    assert canonicalize_name("Python 3") == "python 3"
    assert canonicalize_name("") == ""
    assert canonicalize_name(None) == ""  # type: ignore[arg-type]


def test_graph_entity_creation_valid() -> None:
    """Verifies valid creation of a GraphEntity domain entity."""
    user_id = uuid4()
    entity = GraphEntity(
        user_id=user_id,
        entity_type=EntityType.SKILL,
        name="  Python  ",
        properties={"category": "Programming Languages"},
    )

    assert entity.user_id == user_id
    assert entity.entity_type == EntityType.SKILL
    assert entity.name == "Python"
    assert entity.canonical_name == "python"
    assert entity.properties == {"category": "Programming Languages"}
    assert entity.id is not None


def test_graph_entity_type_coercion() -> None:
    """Verifies string coercion of entity_type in GraphEntity."""
    user_id = uuid4()
    entity = GraphEntity(
        user_id=user_id,
        entity_type="project",  # type: ignore[arg-type]
        name="ChronicleAI",
    )
    assert entity.entity_type == EntityType.PROJECT


def test_graph_entity_invalid_name() -> None:
    """Verifies validation failure when entity name is empty or whitespace."""
    user_id = uuid4()
    with pytest.raises(DomainValidationError, match="Entity name cannot be empty"):
        GraphEntity(
            user_id=user_id,
            entity_type=EntityType.SKILL,
            name="   ",
        )


def test_graph_entity_invalid_user_id() -> None:
    """Verifies validation failure when user_id is invalid."""
    with pytest.raises(DomainValidationError, match="user_id must be a valid UUID"):
        GraphEntity(
            user_id="invalid-uuid",  # type: ignore[arg-type]
            entity_type=EntityType.SKILL,
            name="Python",
        )


def test_graph_relationship_creation_valid() -> None:
    """Verifies valid creation of a GraphRelationship domain edge."""
    user_id = uuid4()
    source_id = uuid4()
    target_id = uuid4()

    rel = GraphRelationship(
        user_id=user_id,
        source_entity_id=source_id,
        target_entity_id=target_id,
        relationship_type=RelationshipType.USES,
        weight=2.5,
    )

    assert rel.user_id == user_id
    assert rel.source_entity_id == source_id
    assert rel.target_entity_id == target_id
    assert rel.relationship_type == RelationshipType.USES
    assert rel.weight == 2.5


def test_graph_relationship_self_referential_invalid() -> None:
    """Verifies self-referential relationships are rejected."""
    user_id = uuid4()
    same_id = uuid4()

    with pytest.raises(DomainValidationError, match="Self-referential relationships are not permitted"):
        GraphRelationship(
            user_id=user_id,
            source_entity_id=same_id,
            target_entity_id=same_id,
            relationship_type=RelationshipType.USES,
        )


def test_graph_relationship_type_coercion() -> None:
    """Verifies string coercion of relationship_type in GraphRelationship."""
    user_id = uuid4()
    source_id = uuid4()
    target_id = uuid4()

    rel = GraphRelationship(
        user_id=user_id,
        source_entity_id=source_id,
        target_entity_id=target_id,
        relationship_type="worked_at",  # type: ignore[arg-type]
    )
    assert rel.relationship_type == RelationshipType.WORKED_AT


def test_graph_relationship_invalid_type_raises() -> None:
    """Verifies invalid relationship type raises error."""
    with pytest.raises(ValueError, match="Unsupported relationship type"):
        RelationshipType.from_string("INVALID_TYPE")


def test_graph_provenance_creation_and_serialization() -> None:
    """Verifies creation and serialization of GraphProvenance value object."""
    artifact_id = uuid4()
    extraction_id = uuid4()

    prov = GraphProvenance(
        artifact_id=artifact_id,
        extraction_id=extraction_id,
        confidence="HIGH",
        evidence_snippet="Worked as Python Developer",
        source_location="work_experience[0]",
    )

    assert prov.artifact_id == artifact_id
    assert prov.extraction_id == extraction_id
    assert prov.confidence == "HIGH"

    d = prov.to_dict()
    assert d["artifact_id"] == str(artifact_id)
    assert d["extraction_id"] == str(extraction_id)
    assert d["confidence"] == "HIGH"
    assert d["evidence_snippet"] == "Worked as Python Developer"


def test_graph_exceptions() -> None:
    """Verifies domain graph exceptions format error messages properly."""
    exc1 = GraphEntityNotFoundError("Entity missing.")
    assert exc1.message == "Entity missing."

    exc2 = GraphRelationshipNotFoundError("Edge missing.")
    assert exc2.message == "Edge missing."
