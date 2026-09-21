"""Unit tests for ExtractionGraphMapper permitted and prohibited relationship semantics."""

from uuid import uuid4
import pytest

from app.application.knowledge_graph.extraction_graph_mapper import (
    ExtractionGraphMapper,
    _category_to_entity_type,
)
from app.domain.value_objects.classification_result import ConfidenceLevel
from app.domain.value_objects.document_type import DocumentType
from app.domain.value_objects.entity_type import EntityType
from app.domain.value_objects.extraction_result import ExtractionResult, ExtractionStatus
from app.domain.value_objects.relationship_type import RelationshipType


def test_category_to_entity_type_valid_skills() -> None:
    """Verifies recognized skill category strings map to EntityType.SKILL."""
    for cat in ["skill", "skills", "soft skill", "soft_skill", "hard skill", "hard_skill", "competency"]:
        assert _category_to_entity_type(cat) == EntityType.SKILL
        assert _category_to_entity_type(cat.upper()) == EntityType.SKILL


def test_category_to_entity_type_valid_technologies() -> None:
    """Verifies recognized technology category strings map to EntityType.TECHNOLOGY."""
    for cat in ["technology", "technologies", "tech", "tool", "tools", "framework", "frameworks", "library", "libraries", "language", "languages", "platform", "platforms", "database", "databases", "infrastructure"]:
        assert _category_to_entity_type(cat) == EntityType.TECHNOLOGY
        assert _category_to_entity_type(cat.upper()) == EntityType.TECHNOLOGY


def test_category_to_entity_type_unknown_raises_value_error() -> None:
    """Verifies unknown category strings raise ValueError without silent fallback."""
    with pytest.raises(ValueError, match="Unrecognised extraction category 'unknown_cat'"):
        _category_to_entity_type("unknown_cat")


def test_role_uses_skill_and_technology() -> None:
    """Verifies experience skills map to ROLE -> USES -> SKILL/TECHNOLOGY."""
    user_id = uuid4()
    artifact_id = uuid4()
    result = ExtractionResult(
        artifact_id=artifact_id,
        document_type=DocumentType.resume(),
        structured_data={
            "experience": [
                {
                    "role": "Senior Engineer",
                    "company": "Acme Corp",
                    "skills": [
                        {"name": "Python", "category": "technology"},
                        {"name": "Leadership", "category": "skill"},
                    ],
                }
            ]
        },
        confidence=ConfidenceLevel.HIGH,
        status=ExtractionStatus.SUCCESS,
    )
    mapper = ExtractionGraphMapper()
    candidates = mapper.map_extraction_to_graph(user_id, artifact_id, None, result)

    role_entity = next(e for e in candidates.entities if e.entity_type == EntityType.ROLE)
    tech_entity = next(e for e in candidates.entities if e.entity_type == EntityType.TECHNOLOGY and e.canonical_name == "python")
    skill_entity = next(e for e in candidates.entities if e.entity_type == EntityType.SKILL and e.canonical_name == "leadership")

    # ROLE -> USES -> TECHNOLOGY
    rel_tech = next(r for r in candidates.relationships if r.source_entity_id == role_entity.id and r.target_entity_id == tech_entity.id)
    assert rel_tech.relationship_type == RelationshipType.USES

    # ROLE -> USES -> SKILL
    rel_skill = next(r for r in candidates.relationships if r.source_entity_id == role_entity.id and r.target_entity_id == skill_entity.id)
    assert rel_skill.relationship_type == RelationshipType.USES


def test_no_company_uses_skill_or_technology() -> None:
    """Verifies mapper NEVER produces COMPANY -> USES -> SKILL/TECHNOLOGY edges (prohibited relationship)."""
    user_id = uuid4()
    artifact_id = uuid4()
    result = ExtractionResult(
        artifact_id=artifact_id,
        document_type=DocumentType.resume(),
        structured_data={
            "experience": [
                {
                    "role": "Data Scientist",
                    "company": "DataCorp",
                    "skills": [{"name": "PyTorch", "category": "technology"}],
                }
            ]
        },
        confidence=ConfidenceLevel.HIGH,
        status=ExtractionStatus.SUCCESS,
    )
    mapper = ExtractionGraphMapper()
    candidates = mapper.map_extraction_to_graph(user_id, artifact_id, None, result)

    company_ids = {e.id for e in candidates.entities if e.entity_type == EntityType.COMPANY}

    for rel in candidates.relationships:
        if rel.relationship_type == RelationshipType.USES:
            assert rel.source_entity_id not in company_ids, "COMPANY must NEVER be the source of a USES edge"


def test_project_related_to_role_only_when_explicit() -> None:
    """Verifies PROJECT -> RELATED_TO -> ROLE is created ONLY when explicit role_ref exists,
    and NOT when role_ref is absent even if they share technologies.
    """
    user_id = uuid4()
    artifact_id = uuid4()

    # Case 1: Explicit role_ref
    result_explicit = ExtractionResult(
        artifact_id=artifact_id,
        document_type=DocumentType.resume(),
        structured_data={
            "experience": [{"role": "Senior Engineer", "company": "Acme Corp"}],
            "projects": [
                {
                    "title": "Cloud Migrator",
                    "role_ref": "Senior Engineer",
                    "technologies": [{"name": "AWS", "category": "technology"}],
                }
            ],
        },
        confidence=ConfidenceLevel.HIGH,
        status=ExtractionStatus.SUCCESS,
    )
    mapper = ExtractionGraphMapper()
    candidates_explicit = mapper.map_extraction_to_graph(user_id, artifact_id, None, result_explicit)

    related_rels = [r for r in candidates_explicit.relationships if r.relationship_type == RelationshipType.RELATED_TO]
    assert len(related_rels) == 1

    # Case 2: No explicit role_ref — prohibited to infer
    result_no_ref = ExtractionResult(
        artifact_id=artifact_id,
        document_type=DocumentType.resume(),
        structured_data={
            "experience": [{"role": "Senior Engineer", "company": "Acme Corp"}],
            "projects": [
                {
                    "title": "Cloud Migrator",
                    "technologies": [{"name": "AWS", "category": "technology"}],
                }
            ],
        },
        confidence=ConfidenceLevel.HIGH,
        status=ExtractionStatus.SUCCESS,
    )
    candidates_no_ref = mapper.map_extraction_to_graph(user_id, artifact_id, None, result_no_ref)
    related_rels_absent = [r for r in candidates_no_ref.relationships if r.relationship_type == RelationshipType.RELATED_TO]
    assert len(related_rels_absent) == 0
