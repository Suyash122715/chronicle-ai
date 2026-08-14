"""Unit tests for ArtifactExtractionModel ORM mapping and domain conversion."""

from datetime import datetime, timezone
from uuid import uuid4

from app.domain.value_objects.classification_result import ConfidenceLevel
from app.domain.value_objects.document_type import DocumentType
from app.domain.value_objects.extraction_result import ExtractionResult, ExtractionStatus
from app.domain.value_objects.provenance import Provenance
from app.infrastructure.db.models.artifact_extraction_model import ArtifactExtractionModel


def test_artifact_extraction_model_from_domain() -> None:
    """Verifies conversion from ExtractionResult domain object to ArtifactExtractionModel ORM instance."""
    artifact_id = uuid4()
    now = datetime.now(timezone.utc)

    provenance_map = {
        "name": Provenance(artifact_id=artifact_id, evidence_snippet="John Doe", confidence="HIGH"),
        "email": Provenance(artifact_id=artifact_id, evidence_snippet="john@example.com", confidence="HIGH"),
    }

    result = ExtractionResult(
        artifact_id=artifact_id,
        document_type=DocumentType.resume(),
        structured_data={"contact_information": {"name": "John Doe", "email": "john@example.com"}},
        provenance=provenance_map,
        warnings=["Non-fatal extraction warning"],
        confidence=ConfidenceLevel.HIGH,
        extractor_version="1.0.0",
        prompt_version="v1",
        llm_metadata={"provider": "mock_provider", "latency_ms": 150.0},
        started_at=now,
        completed_at=now,
        status=ExtractionStatus.SUCCESS,
        error_message=None,
    )

    model = ArtifactExtractionModel.from_domain(result)

    assert model.artifact_id == artifact_id
    assert model.document_type == "Resume"
    assert model.status == "SUCCESS"
    assert model.structured_data == {"contact_information": {"name": "John Doe", "email": "john@example.com"}}
    assert "name" in model.provenance
    assert model.provenance["name"]["evidence_snippet"] == "John Doe"
    assert model.warnings == ["Non-fatal extraction warning"]
    assert model.confidence == "HIGH"
    assert model.extractor_version == "1.0.0"
    assert model.prompt_version == "v1"
    assert model.llm_metadata["provider"] == "mock_provider"
    assert model.error_message is None


def test_artifact_extraction_model_to_domain() -> None:
    """Verifies conversion from ArtifactExtractionModel ORM instance to ExtractionResult domain object."""
    artifact_id = uuid4()
    now = datetime.now(timezone.utc)

    model = ArtifactExtractionModel(
        id=uuid4(),
        artifact_id=artifact_id,
        document_type="GitHub Repository",
        status="SUCCESS",
        structured_data={"repository_info": {"name": "chronicle-ai"}},
        provenance={
            "name": {
                "artifact_id": str(artifact_id),
                "evidence_snippet": "chronicle-ai",
                "confidence": "HIGH",
            }
        },
        warnings=[],
        confidence="HIGH",
        extractor_version="1.0.0",
        prompt_version="v1",
        llm_metadata={"provider": "gemini", "model": "gemini-1.5-flash"},
        error_message=None,
        started_at=now,
        completed_at=now,
    )

    result = model.to_domain()

    assert isinstance(result, ExtractionResult)
    assert result.artifact_id == artifact_id
    assert result.document_type == DocumentType.github_repository()
    assert result.status == ExtractionStatus.SUCCESS
    assert result.structured_data == {"repository_info": {"name": "chronicle-ai"}}
    assert "name" in result.provenance
    assert isinstance(result.provenance["name"], Provenance)
    assert result.provenance["name"].evidence_snippet == "chronicle-ai"
    assert result.confidence == ConfidenceLevel.HIGH
    assert result.extractor_version == "1.0.0"
    assert result.prompt_version == "v1"
    assert result.llm_metadata["provider"] == "gemini"
