"""Unit tests for the provenance value object."""

from uuid import uuid4

from app.domain.value_objects import Provenance


def test_provenance_serializes_uuid_and_optional_evidence() -> None:
    artifact_id = uuid4()
    provenance = Provenance(
        artifact_id=artifact_id,
        page_reference="page 2",
        section_reference="Experience",
        evidence_snippet="Built an API with FastAPI.",
        evidence_location="paragraph 4",
        confidence="high",
        extraction_version="2026.08",
    )

    assert provenance.to_dict() == {
        "artifact_id": str(artifact_id),
        "page_reference": "page 2",
        "section_reference": "Experience",
        "evidence_snippet": "Built an API with FastAPI.",
        "evidence_location": "paragraph 4",
        "confidence": "high",
        "extraction_version": "2026.08",
    }


def test_provenance_defaults_optional_fields() -> None:
    provenance = Provenance(artifact_id=uuid4())

    assert provenance.page_reference is None
    assert provenance.section_reference is None
    assert provenance.evidence_snippet is None
    assert provenance.evidence_location is None
    assert provenance.confidence == "low"
    assert provenance.extraction_version == "unknown"
