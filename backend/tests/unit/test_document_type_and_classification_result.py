"""Unit tests for DocumentType and ClassificationResult value objects."""

from datetime import datetime, timezone
import uuid
import pytest

from app.domain.value_objects.classification_result import ClassificationResult, ConfidenceLevel
from app.domain.value_objects.document_type import DocumentType, DocumentTypeEnum
from app.domain.value_objects.provenance import Provenance


class TestDocumentType:
    """Test suite for DocumentType domain value object."""

    def test_factory_methods(self) -> None:
        """Verifies factory methods produce expected enum values and string representations."""
        assert DocumentType.resume().value == "Resume"
        assert DocumentType.certificate().value == "Certificate"
        assert DocumentType.marksheet().value == "Marksheet"
        assert DocumentType.internship_letter().value == "Internship Letter"
        assert DocumentType.project_report().value == "Project Report"
        assert DocumentType.github_repository().value == "GitHub Repository"
        assert DocumentType.portfolio().value == "Portfolio"
        assert DocumentType.unknown().value == "Unknown"

    def test_from_str_valid_cases(self) -> None:
        """Verifies case-insensitive parsing of valid document type strings."""
        assert DocumentType.from_str("resume") == DocumentType.resume()
        assert DocumentType.from_str("CERTIFICATE") == DocumentType.certificate()
        assert DocumentType.from_str("  Marksheet  ") == DocumentType.marksheet()
        assert DocumentType.from_str("internship letter") == DocumentType.internship_letter()
        assert DocumentType.from_str("project report") == DocumentType.project_report()
        assert DocumentType.from_str("github repository") == DocumentType.github_repository()
        assert DocumentType.from_str("portfolio") == DocumentType.portfolio()

    def test_from_str_invalid_falls_back_to_unknown(self) -> None:
        """Verifies unrecognized string inputs parse to UNKNOWN."""
        assert DocumentType.from_str("invalid_doc_type") == DocumentType.unknown()
        assert DocumentType.from_str("") == DocumentType.unknown()

    def test_equality_comparisons(self) -> None:
        """Verifies equality comparison with other DocumentType instances, Enums, and strings."""
        doc = DocumentType.resume()
        assert doc == DocumentType.resume()
        assert doc == DocumentTypeEnum.RESUME
        assert doc == "Resume"
        assert doc == "resume"
        assert doc != DocumentType.certificate()
        assert doc != "Certificate"
        assert doc != 12345

    def test_is_known(self) -> None:
        """Verifies is_known behavior across document types."""
        assert DocumentType.resume().is_known() is True
        assert DocumentType.unknown().is_known() is False

    def test_hashable(self) -> None:
        """Verifies DocumentType can be used in sets and dict keys."""
        doc_set = {DocumentType.resume(), DocumentType.resume(), DocumentType.certificate()}
        assert len(doc_set) == 2
        assert DocumentType.resume() in doc_set


class TestClassificationResult:
    """Test suite for ClassificationResult value object."""

    def test_immutability(self) -> None:
        """Verifies ClassificationResult is immutable and raises FrozenInstanceError on modification."""
        artifact_id = uuid.uuid4()
        provenance = Provenance(artifact_id=artifact_id, confidence="HIGH")
        result = ClassificationResult(
            document_type=DocumentType.resume(),
            confidence_level=ConfidenceLevel.HIGH,
            classifier_version="deterministic-1.0",
            classified_at=datetime.now(timezone.utc),
            provenance=provenance,
        )

        with pytest.raises(AttributeError):
            result.confidence_level = ConfidenceLevel.LOW  # type: ignore

    def test_to_dict_serialization(self) -> None:
        """Verifies serialization format of ClassificationResult."""
        artifact_id = uuid.uuid4()
        now = datetime.now(timezone.utc)
        provenance = Provenance(
            artifact_id=artifact_id,
            evidence_snippet="Matched resume keyword in filename",
            confidence="HIGH",
        )
        result = ClassificationResult(
            document_type=DocumentType.resume(),
            confidence_level=ConfidenceLevel.HIGH,
            classifier_version="deterministic-1.0",
            classified_at=now,
            provenance=provenance,
        )

        serialized = result.to_dict()
        assert serialized["document_type"] == "Resume"
        assert serialized["confidence_level"] == "HIGH"
        assert serialized["classifier_version"] == "deterministic-1.0"
        assert serialized["classified_at"] == now.isoformat()
        assert serialized["provenance"]["artifact_id"] == str(artifact_id)
