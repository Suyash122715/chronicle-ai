"""Unit tests for ExtractionGraphMapper and BuildKnowledgeGraphUseCase."""

from uuid import uuid4
import pytest

from app.application.knowledge_graph.build_knowledge_graph_use_case import BuildKnowledgeGraphUseCase
from app.application.knowledge_graph.extraction_graph_mapper import ExtractionGraphMapper
from app.domain.exceptions.base import DomainValidationError
from app.domain.value_objects.classification_result import ConfidenceLevel
from app.domain.value_objects.document_type import DocumentType
from app.domain.value_objects.entity_type import EntityType
from app.domain.value_objects.extraction_result import ExtractionResult, ExtractionStatus
from app.domain.value_objects.provenance import Provenance
from app.domain.value_objects.relationship_type import RelationshipType


def test_mapper_entity_and_relationship_types_resume() -> None:
    """Verifies resume extraction mapping to SKILL, COMPANY, ROLE, PROJECT, and relationships."""
    user_id = uuid4()
    artifact_id = uuid4()
    extraction_id = uuid4()

    structured_data = {
        "skills": ["Python", "  FastAPI  ", "PostgreSQL"],
        "experience": [
            {"company": "Acme Corp", "role": "Senior Engineer"},
        ],
        "projects": [
            {"title": "ChronicleAI", "description": "AI Document Processing", "technologies": ["Python", "React"]},
        ],
    }

    result = ExtractionResult(
        artifact_id=artifact_id,
        document_type=DocumentType.resume(),
        structured_data=structured_data,
        confidence=ConfidenceLevel.HIGH,
        status=ExtractionStatus.SUCCESS,
    )

    mapper = ExtractionGraphMapper()
    candidates = mapper.map_extraction_to_graph(
        user_id=user_id,
        artifact_id=artifact_id,
        extraction_id=extraction_id,
        extraction_result=result,
    )

    # Check entity types
    entity_types = {e.entity_type for e in candidates.entities}
    assert EntityType.SKILL in entity_types
    assert EntityType.COMPANY in entity_types
    assert EntityType.ROLE in entity_types
    assert EntityType.PROJECT in entity_types
    assert EntityType.TECHNOLOGY in entity_types

    # Check specific typed entity deduplication (SKILL vs TECHNOLOGY coexist, identical type deduplicates)
    skill_python = [e for e in candidates.entities if e.entity_type == EntityType.SKILL and e.canonical_name == "python"]
    tech_python = [e for e in candidates.entities if e.entity_type == EntityType.TECHNOLOGY and e.canonical_name == "python"]
    assert len(skill_python) == 1
    assert len(tech_python) == 1

    # Check relationship mapping
    rel_types = {r.relationship_type for r in candidates.relationships}
    assert RelationshipType.HELD_ROLE in rel_types
    assert RelationshipType.USES in rel_types

    # Check user ownership
    for entity in candidates.entities:
        assert entity.user_id == user_id
    for rel in candidates.relationships:
        assert rel.user_id == user_id


def test_mapper_certificate_extraction() -> None:
    """Verifies certificate extraction mapping to CERTIFICATE, COMPANY, SKILL, and ISSUED_BY."""
    user_id = uuid4()
    artifact_id = uuid4()
    extraction_id = uuid4()

    structured_data = {
        "certificate_info": {
            "title": "AWS Certified Solutions Architect",
            "issuer": "Amazon Web Services",
        },
        "skills": ["Cloud Architecture", "AWS"],
    }

    result = ExtractionResult(
        artifact_id=artifact_id,
        document_type=DocumentType.certificate(),
        structured_data=structured_data,
        confidence=ConfidenceLevel.HIGH,
        status=ExtractionStatus.SUCCESS,
    )

    mapper = ExtractionGraphMapper()
    candidates = mapper.map_extraction_to_graph(
        user_id=user_id,
        artifact_id=artifact_id,
        extraction_id=extraction_id,
        extraction_result=result,
    )

    cert_entity = next(e for e in candidates.entities if e.entity_type == EntityType.CERTIFICATE)
    issuer_entity = next(e for e in candidates.entities if e.entity_type == EntityType.COMPANY)

    assert cert_entity.name == "AWS Certified Solutions Architect"
    assert issuer_entity.name == "Amazon Web Services"

    # Check ISSUED_BY relationship
    rel = next(r for r in candidates.relationships if r.relationship_type == RelationshipType.ISSUED_BY)
    assert rel.source_entity_id == cert_entity.id
    assert rel.target_entity_id == issuer_entity.id


def test_mapper_marksheet_extraction() -> None:
    """Verifies marksheet extraction mapping to INSTITUTION, ROLE, and STUDIED_AT."""
    user_id = uuid4()
    artifact_id = uuid4()

    structured_data = {
        "academic_info": {
            "institution": "Stanford University",
            "program": "Computer Science B.S.",
        }
    }

    result = ExtractionResult(
        artifact_id=artifact_id,
        document_type=DocumentType.marksheet(),
        structured_data=structured_data,
        status=ExtractionStatus.SUCCESS,
    )

    mapper = ExtractionGraphMapper()
    candidates = mapper.map_extraction_to_graph(user_id, artifact_id, None, result)

    inst_entity = next(e for e in candidates.entities if e.entity_type == EntityType.INSTITUTION)
    prog_entity = next(e for e in candidates.entities if e.entity_type == EntityType.ROLE)

    assert inst_entity.name == "Stanford University"
    assert prog_entity.name == "Computer Science B.S."

    rel = next(r for r in candidates.relationships if r.relationship_type == RelationshipType.STUDIED_AT)
    assert rel.source_entity_id == prog_entity.id
    assert rel.target_entity_id == inst_entity.id


def test_mapper_project_report_and_outcomes() -> None:
    """Verifies project report mapping to PROJECT, ACHIEVEMENT, and CREATED relationship."""
    user_id = uuid4()
    artifact_id = uuid4()

    structured_data = {
        "project_info": {"title": "Distributed Database Engine", "description": "High throughput key-value store"},
        "outcomes": ["Reduced latency by 45%", "Published technical whitepaper"],
    }

    result = ExtractionResult(
        artifact_id=artifact_id,
        document_type=DocumentType.project_report(),
        structured_data=structured_data,
        status=ExtractionStatus.SUCCESS,
    )

    mapper = ExtractionGraphMapper()
    candidates = mapper.map_extraction_to_graph(user_id, artifact_id, None, result)

    proj_entity = next(e for e in candidates.entities if e.entity_type == EntityType.PROJECT)
    achievements = [e for e in candidates.entities if e.entity_type == EntityType.ACHIEVEMENT]

    assert len(achievements) == 2
    assert proj_entity.name == "Distributed Database Engine"

    created_rels = [r for r in candidates.relationships if r.relationship_type == RelationshipType.CREATED]
    assert len(created_rels) == 2


def test_mapper_deduplication_case_and_whitespace() -> None:
    """Verifies case and whitespace normalization deduplicates entities and edges."""
    user_id = uuid4()
    artifact_id = uuid4()

    structured_data = {
        "skills": ["Python", " python ", "PYTHON", "REACT", "React"],
    }

    result = ExtractionResult(
        artifact_id=artifact_id,
        document_type=DocumentType.resume(),
        structured_data=structured_data,
        status=ExtractionStatus.SUCCESS,
    )

    mapper = ExtractionGraphMapper()
    candidates = mapper.map_extraction_to_graph(user_id, artifact_id, None, result)

    assert len(candidates.entities) == 2
    canonical_names = {e.canonical_name for e in candidates.entities}
    assert canonical_names == {"python", "react"}


def test_mapper_status_handling() -> None:
    """Verifies FAILED, NOT_SUPPORTED, SKIPPED produce zero graph candidates, while PARTIAL builds available data."""
    user_id = uuid4()
    artifact_id = uuid4()
    mapper = ExtractionGraphMapper()

    for status in (ExtractionStatus.FAILED, ExtractionStatus.NOT_SUPPORTED, ExtractionStatus.SKIPPED):
        result = ExtractionResult(
            artifact_id=artifact_id,
            document_type=DocumentType.resume(),
            structured_data={"skills": ["Python"]},
            status=status,
        )
        candidates = mapper.map_extraction_to_graph(user_id, artifact_id, None, result)
        assert len(candidates.entities) == 0
        assert len(candidates.relationships) == 0

    # PARTIAL status builds available entities
    partial_result = ExtractionResult(
        artifact_id=artifact_id,
        document_type=DocumentType.resume(),
        structured_data={"skills": ["Python"]},
        status=ExtractionStatus.PARTIAL,
    )
    partial_candidates = mapper.map_extraction_to_graph(user_id, artifact_id, None, partial_result)
    assert len(partial_candidates.entities) == 1


def test_mapper_provenance_preservation() -> None:
    """Verifies GraphProvenance entries preserve artifact_id, extraction_id, confidence, and source_location."""
    user_id = uuid4()
    artifact_id = uuid4()
    extraction_id = uuid4()

    provenance_map = {
        "skills[0]": Provenance(artifact_id=artifact_id, evidence_snippet="Expert in Python"),
    }

    result = ExtractionResult(
        artifact_id=artifact_id,
        document_type=DocumentType.resume(),
        structured_data={"skills": ["Python"]},
        provenance=provenance_map,
        confidence=ConfidenceLevel.HIGH,
        status=ExtractionStatus.SUCCESS,
    )

    mapper = ExtractionGraphMapper()
    candidates = mapper.map_extraction_to_graph(user_id, artifact_id, extraction_id, result)

    entity = candidates.entities[0]
    prov = candidates.entity_provenance[entity.id]

    assert prov.artifact_id == artifact_id
    assert prov.extraction_id == extraction_id
    assert prov.confidence == "HIGH"
    assert prov.extraction_method == "LLM_EXTRACTION"
    assert prov.source_location == "skills[0]"


def test_build_knowledge_graph_use_case_validation() -> None:
    """Verifies BuildKnowledgeGraphUseCase validates artifact_id matching."""
    user_id = uuid4()
    artifact_id_1 = uuid4()
    artifact_id_2 = uuid4()

    result = ExtractionResult(
        artifact_id=artifact_id_1,
        document_type=DocumentType.resume(),
        structured_data={"skills": ["Python"]},
        status=ExtractionStatus.SUCCESS,
    )

    use_case = BuildKnowledgeGraphUseCase()

    # Mismatched artifact_id raises DomainValidationError
    with pytest.raises(DomainValidationError, match="Extraction artifact ID mismatch"):
        use_case.execute(user_id=user_id, artifact_id=artifact_id_2, extraction_result=result)

    # Valid matching artifact_id succeeds
    candidates = use_case.execute(user_id=user_id, artifact_id=artifact_id_1, extraction_result=result)
    assert len(candidates.entities) == 1


# =============================================================================
# Batch 3 Regression Tests
# =============================================================================


def test_held_role_direction() -> None:
    """Verifies HELD_ROLE edge runs ROLE --[HELD_ROLE]--> COMPANY, not the inverse."""
    user_id = uuid4()
    artifact_id = uuid4()

    structured_data = {
        "experience": [
            {"company": "Acme Corp", "role": "Senior Engineer"},
        ],
    }

    result = ExtractionResult(
        artifact_id=artifact_id,
        document_type=DocumentType.resume(),
        structured_data=structured_data,
        status=ExtractionStatus.SUCCESS,
    )

    mapper = ExtractionGraphMapper()
    candidates = mapper.map_extraction_to_graph(user_id, artifact_id, None, result)

    role_entity = next(e for e in candidates.entities if e.entity_type == EntityType.ROLE)
    comp_entity = next(e for e in candidates.entities if e.entity_type == EntityType.COMPANY)

    rel = next(r for r in candidates.relationships if r.relationship_type == RelationshipType.HELD_ROLE)
    assert rel.source_entity_id == role_entity.id, "HELD_ROLE source must be ROLE"
    assert rel.target_entity_id == comp_entity.id, "HELD_ROLE target must be COMPANY"


def test_held_role_direction_internship_info() -> None:
    """Verifies HELD_ROLE edge direction is correct for the internship_info mapping path."""
    user_id = uuid4()
    artifact_id = uuid4()

    structured_data = {
        "internship_info": {
            "organization": "ByteCorp",
            "role": "ML Intern",
        },
    }

    result = ExtractionResult(
        artifact_id=artifact_id,
        document_type=DocumentType.internship_letter(),
        structured_data=structured_data,
        status=ExtractionStatus.SUCCESS,
    )

    mapper = ExtractionGraphMapper()
    candidates = mapper.map_extraction_to_graph(user_id, artifact_id, None, result)

    role_entity = next(e for e in candidates.entities if e.entity_type == EntityType.ROLE)
    comp_entity = next(e for e in candidates.entities if e.entity_type == EntityType.COMPANY)

    rel = next(r for r in candidates.relationships if r.relationship_type == RelationshipType.HELD_ROLE)
    assert rel.source_entity_id == role_entity.id, "HELD_ROLE source must be ROLE"
    assert rel.target_entity_id == comp_entity.id, "HELD_ROLE target must be COMPANY"


def test_studied_at_direction_education_list() -> None:
    """Verifies STUDIED_AT edge runs ROLE --[STUDIED_AT]--> INSTITUTION via education[] list path."""
    user_id = uuid4()
    artifact_id = uuid4()

    structured_data = {
        "education": [
            {"institution": "MIT", "program": "Computer Science M.S."},
        ],
    }

    result = ExtractionResult(
        artifact_id=artifact_id,
        document_type=DocumentType.resume(),
        structured_data=structured_data,
        status=ExtractionStatus.SUCCESS,
    )

    mapper = ExtractionGraphMapper()
    candidates = mapper.map_extraction_to_graph(user_id, artifact_id, None, result)

    inst_entity = next(e for e in candidates.entities if e.entity_type == EntityType.INSTITUTION)
    prog_entity = next(e for e in candidates.entities if e.entity_type == EntityType.ROLE)

    rel = next(r for r in candidates.relationships if r.relationship_type == RelationshipType.STUDIED_AT)
    assert rel.source_entity_id == prog_entity.id, "STUDIED_AT source must be ROLE (program)"
    assert rel.target_entity_id == inst_entity.id, "STUDIED_AT target must be INSTITUTION"


def test_none_in_project_technologies_does_not_crash() -> None:
    """Verifies None entries in project technologies[] are skipped without crashing."""
    user_id = uuid4()
    artifact_id = uuid4()

    structured_data = {
        "projects": [
            {
                "title": "MyApp",
                "technologies": [None, "React", None, "TypeScript"],
            }
        ],
    }

    result = ExtractionResult(
        artifact_id=artifact_id,
        document_type=DocumentType.resume(),
        structured_data=structured_data,
        status=ExtractionStatus.SUCCESS,
    )

    mapper = ExtractionGraphMapper()
    candidates = mapper.map_extraction_to_graph(user_id, artifact_id, None, result)

    tech_names = {e.canonical_name for e in candidates.entities if e.entity_type == EntityType.TECHNOLOGY}
    assert "react" in tech_names
    assert "typescript" in tech_names
    # None entries must not produce any entity
    assert len(tech_names) == 2


def test_none_in_github_languages_does_not_crash() -> None:
    """Verifies None entries in GitHub repository languages[] are skipped without crashing."""
    user_id = uuid4()
    artifact_id = uuid4()

    structured_data = {
        "repository_info": {"name": "my-repo", "description": "Demo"},
        "languages": ["Python", None, "Go"],
    }

    result = ExtractionResult(
        artifact_id=artifact_id,
        document_type=DocumentType.github_repository(),
        structured_data=structured_data,
        status=ExtractionStatus.SUCCESS,
    )

    mapper = ExtractionGraphMapper()
    candidates = mapper.map_extraction_to_graph(user_id, artifact_id, None, result)

    tech_names = {e.canonical_name for e in candidates.entities if e.entity_type == EntityType.TECHNOLOGY}
    assert "python" in tech_names
    assert "go" in tech_names
    # None entry must not produce any entity
    assert len(tech_names) == 2


def test_malformed_technology_entry_does_not_crash() -> None:
    """Verifies non-string, non-dict entries (integers, booleans) in technologies[] are skipped."""
    user_id = uuid4()
    artifact_id = uuid4()

    structured_data = {
        "projects": [
            {
                "title": "DataPipeline",
                # Mix of valid string, malformed integer, None, and valid dict
                "technologies": ["Kafka", 42, None, {"name": "Spark"}, True],
            }
        ],
    }

    result = ExtractionResult(
        artifact_id=artifact_id,
        document_type=DocumentType.resume(),
        structured_data=structured_data,
        status=ExtractionStatus.SUCCESS,
    )

    mapper = ExtractionGraphMapper()
    candidates = mapper.map_extraction_to_graph(user_id, artifact_id, None, result)

    tech_names = {e.canonical_name for e in candidates.entities if e.entity_type == EntityType.TECHNOLOGY}
    assert "kafka" in tech_names
    assert "spark" in tech_names
    # Integer 42, None, and True must all be silently skipped
    assert len(tech_names) == 2


def test_empty_structured_data_returns_empty_candidates() -> None:
    """Verifies that structured_data={} produces zero entities and zero relationships."""
    user_id = uuid4()
    artifact_id = uuid4()

    result = ExtractionResult(
        artifact_id=artifact_id,
        document_type=DocumentType.resume(),
        structured_data={},
        status=ExtractionStatus.SUCCESS,
    )

    mapper = ExtractionGraphMapper()
    candidates = mapper.map_extraction_to_graph(user_id, artifact_id, None, result)

    assert len(candidates.entities) == 0
    assert len(candidates.relationships) == 0
    assert len(candidates.entity_provenance) == 0
    assert len(candidates.relationship_provenance) == 0


def test_extraction_id_none_provenance() -> None:
    """Verifies extraction_id=None is correctly preserved in both entity and relationship provenance."""
    user_id = uuid4()
    artifact_id = uuid4()

    structured_data = {
        "skills": ["Rust"],
        "experience": [{"company": "WidgetCo", "role": "Engineer"}],
    }

    result = ExtractionResult(
        artifact_id=artifact_id,
        document_type=DocumentType.resume(),
        structured_data=structured_data,
        status=ExtractionStatus.SUCCESS,
    )

    mapper = ExtractionGraphMapper()
    # Explicitly pass extraction_id=None
    candidates = mapper.map_extraction_to_graph(user_id, artifact_id, None, result)

    for prov in candidates.entity_provenance.values():
        assert prov.extraction_id is None
    for prov in candidates.relationship_provenance.values():
        assert prov.extraction_id is None


def test_portfolio_work_experience_mapping() -> None:
    """Verifies Portfolio work_experience key maps correctly to ROLE --[HELD_ROLE]--> COMPANY."""
    user_id = uuid4()
    artifact_id = uuid4()

    structured_data = {
        "work_experience": [
            {"company": "StartupXYZ", "role": "Full-Stack Developer"},
            {"company": "AgencyABC", "title": "Lead Designer"},
        ],
    }

    result = ExtractionResult(
        artifact_id=artifact_id,
        document_type=DocumentType.portfolio(),
        structured_data=structured_data,
        status=ExtractionStatus.SUCCESS,
    )

    mapper = ExtractionGraphMapper()
    candidates = mapper.map_extraction_to_graph(user_id, artifact_id, None, result)

    held_role_rels = [r for r in candidates.relationships if r.relationship_type == RelationshipType.HELD_ROLE]
    assert len(held_role_rels) == 2

    company_ids = {e.id for e in candidates.entities if e.entity_type == EntityType.COMPANY}
    role_ids = {e.id for e in candidates.entities if e.entity_type == EntityType.ROLE}

    for rel in held_role_rels:
        assert rel.source_entity_id in role_ids, "HELD_ROLE source must be ROLE"
        assert rel.target_entity_id in company_ids, "HELD_ROLE target must be COMPANY"
