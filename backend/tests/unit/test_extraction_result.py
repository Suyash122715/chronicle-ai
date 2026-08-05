"""Unit tests for canonical ExtractionResult domain value object."""

from dataclasses import FrozenInstanceError
from datetime import datetime, timezone
from uuid import uuid4

import pytest

from app.domain.value_objects import (
    ConfidenceLevel,
    DocumentType,
    ExtractionResult,
    ExtractionStatus,
    Provenance,
)


def test_extraction_result_creation_and_to_dict() -> None:
    artifact_id = uuid4()
    doc_type = DocumentType.resume()
    prov = Provenance(artifact_id=artifact_id, evidence_snippet="Python developer")
    now = datetime.now(timezone.utc)

    result = ExtractionResult(
        artifact_id=artifact_id,
        document_type=doc_type,
        structured_data={"skills": ["Python", "FastAPI"]},
        provenance={"skills[0]": prov},
        warnings=["Non-standard layout"],
        confidence=ConfidenceLevel.HIGH,
        extractor_version="1.0.0",
        prompt_version="v1",
        llm_metadata={"tokens": 150},
        started_at=now,
        completed_at=now,
        status=ExtractionStatus.SUCCESS,
    )

    assert result.artifact_id == artifact_id
    assert result.document_type == doc_type
    assert result.structured_data == {"skills": ["Python", "FastAPI"]}
    assert result.provenance["skills[0]"] == prov
    assert result.warnings == ["Non-standard layout"]
    assert result.confidence == ConfidenceLevel.HIGH
    assert result.extractor_version == "1.0.0"
    assert result.prompt_version == "v1"
    assert result.llm_metadata == {"tokens": 150}
    assert result.status == ExtractionStatus.SUCCESS

    serialized = result.to_dict()
    assert serialized["artifact_id"] == str(artifact_id)
    assert serialized["document_type"] == "Resume"
    assert serialized["structured_data"] == {"skills": ["Python", "FastAPI"]}
    assert "skills[0]" in serialized["provenance"]
    assert serialized["confidence"] == "HIGH"
    assert serialized["status"] == "SUCCESS"


def test_extraction_result_immutability() -> None:
    result = ExtractionResult(
        artifact_id=uuid4(),
        document_type=DocumentType.resume(),
    )
    with pytest.raises(FrozenInstanceError):
        result.status = ExtractionStatus.FAILED  # type: ignore[misc]
