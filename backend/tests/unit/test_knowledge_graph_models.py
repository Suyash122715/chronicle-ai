"""Unit tests for Knowledge Graph SQLAlchemy ORM models mapping and domain conversion."""

from datetime import datetime, timezone
from uuid import uuid4

from app.domain.entities.graph_entity import GraphEntity
from app.domain.entities.graph_relationship import GraphRelationship
from app.domain.value_objects.entity_type import EntityType
from app.domain.value_objects.graph_provenance import GraphProvenance
from app.domain.value_objects.relationship_type import RelationshipType
from app.infrastructure.db.models.entity_artifact_provenance_model import EntityArtifactProvenanceModel
from app.infrastructure.db.models.graph_entity_model import GraphEntityModel
from app.infrastructure.db.models.graph_relationship_model import GraphRelationshipModel
from app.infrastructure.db.models.relationship_artifact_provenance_model import RelationshipArtifactProvenanceModel


def test_graph_entity_model_from_domain_and_to_domain() -> None:
    """Verifies round-trip mapping between GraphEntity domain entity and GraphEntityModel ORM model."""
    user_id = uuid4()
    entity_id = uuid4()
    now = datetime.now(timezone.utc)

    entity = GraphEntity(
        id=entity_id,
        user_id=user_id,
        entity_type=EntityType.SKILL,
        name="  Python  ",
        canonical_name="python",
        properties={"level": "Advanced"},
        created_at=now,
        updated_at=now,
    )

    model = GraphEntityModel.from_domain(entity)
    assert model.id == entity_id
    assert model.user_id == user_id
    assert model.entity_type == "SKILL"
    assert model.name == "Python"
    assert model.canonical_name == "python"
    assert model.properties == {"level": "Advanced"}

    restored_domain = model.to_domain()
    assert isinstance(restored_domain, GraphEntity)
    assert restored_domain.id == entity_id
    assert restored_domain.user_id == user_id
    assert restored_domain.entity_type == EntityType.SKILL
    assert restored_domain.name == "Python"
    assert restored_domain.canonical_name == "python"
    assert restored_domain.properties == {"level": "Advanced"}


def test_graph_relationship_model_from_domain_and_to_domain() -> None:
    """Verifies round-trip mapping between GraphRelationship domain entity and GraphRelationshipModel ORM model."""
    user_id = uuid4()
    source_id = uuid4()
    target_id = uuid4()
    rel_id = uuid4()
    now = datetime.now(timezone.utc)

    rel = GraphRelationship(
        id=rel_id,
        user_id=user_id,
        source_entity_id=source_id,
        target_entity_id=target_id,
        relationship_type=RelationshipType.USES,
        weight=2.0,
        properties={"context": "backend_service"},
        created_at=now,
        updated_at=now,
    )

    model = GraphRelationshipModel.from_domain(rel)
    assert model.id == rel_id
    assert model.user_id == user_id
    assert model.source_entity_id == source_id
    assert model.target_entity_id == target_id
    assert model.relationship_type == "USES"
    assert model.weight == 2.0
    assert model.properties == {"context": "backend_service"}

    restored_domain = model.to_domain()
    assert isinstance(restored_domain, GraphRelationship)
    assert restored_domain.id == rel_id
    assert restored_domain.user_id == user_id
    assert restored_domain.source_entity_id == source_id
    assert restored_domain.target_entity_id == target_id
    assert restored_domain.relationship_type == RelationshipType.USES
    assert restored_domain.weight == 2.0
    assert restored_domain.properties == {"context": "backend_service"}


def test_entity_artifact_provenance_model_mapping() -> None:
    """Verifies mapping between GraphProvenance value object and EntityArtifactProvenanceModel ORM instance."""
    user_id = uuid4()
    entity_id = uuid4()
    artifact_id = uuid4()
    extraction_id = uuid4()

    provenance = GraphProvenance(
        artifact_id=artifact_id,
        extraction_id=extraction_id,
        confidence="HIGH",
        evidence_snippet="Proficient in Python",
        source_location="resume.skills[0]",
        metadata={"section": "Technical Skills"},
    )

    model = EntityArtifactProvenanceModel.from_domain(
        provenance=provenance, entity_id=entity_id, user_id=user_id
    )

    assert model.user_id == user_id
    assert model.entity_id == entity_id
    assert model.artifact_id == artifact_id
    assert model.extraction_id == extraction_id
    assert model.confidence == "HIGH"
    assert model.evidence["evidence_snippet"] == "Proficient in Python"
    assert model.evidence["source_location"] == "resume.skills[0]"

    restored_domain = model.to_domain()
    assert isinstance(restored_domain, GraphProvenance)
    assert restored_domain.artifact_id == artifact_id
    assert restored_domain.extraction_id == extraction_id
    assert restored_domain.confidence == "HIGH"
    assert restored_domain.evidence_snippet == "Proficient in Python"
    assert restored_domain.source_location == "resume.skills[0]"


def test_relationship_artifact_provenance_model_mapping() -> None:
    """Verifies mapping between GraphProvenance value object and RelationshipArtifactProvenanceModel ORM instance."""
    user_id = uuid4()
    relationship_id = uuid4()
    artifact_id = uuid4()
    extraction_id = uuid4()

    provenance = GraphProvenance(
        artifact_id=artifact_id,
        extraction_id=extraction_id,
        confidence="MEDIUM",
        evidence_snippet="Built REST APIs using FastAPI",
        source_location="resume.projects[0]",
        metadata={"project_title": "ChronicleAI"},
    )

    model = RelationshipArtifactProvenanceModel.from_domain(
        provenance=provenance, relationship_id=relationship_id, user_id=user_id
    )

    assert model.user_id == user_id
    assert model.relationship_id == relationship_id
    assert model.artifact_id == artifact_id
    assert model.extraction_id == extraction_id
    assert model.confidence == "MEDIUM"
    assert model.evidence["evidence_snippet"] == "Built REST APIs using FastAPI"

    restored_domain = model.to_domain()
    assert isinstance(restored_domain, GraphProvenance)
    assert restored_domain.artifact_id == artifact_id
    assert restored_domain.extraction_id == extraction_id
    assert restored_domain.confidence == "MEDIUM"
    assert restored_domain.evidence_snippet == "Built REST APIs using FastAPI"
