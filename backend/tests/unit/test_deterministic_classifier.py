"""Unit tests for DeterministicDocumentClassifier and rule precedence."""

import uuid
import pytest

from app.domain.value_objects.classification_result import ConfidenceLevel
from app.domain.value_objects.document_type import DocumentType
from app.infrastructure.processing.deterministic_classifier import (
    DETERMINISTIC_CLASSIFIER_VERSION,
    DeterministicDocumentClassifier,
)


@pytest.mark.asyncio
class TestDeterministicDocumentClassifier:
    """Test suite for DeterministicDocumentClassifier rule engine and precedence."""

    @pytest.fixture
    def classifier(self) -> DeterministicDocumentClassifier:
        return DeterministicDocumentClassifier()

    async def test_rule_precedence_filename_overrides_metadata(
        self, classifier: DeterministicDocumentClassifier
    ) -> None:
        """Verifies Filename rule (Priority 1) overrides Metadata rule (Priority 4)."""
        artifact_id = uuid.uuid4()
        # Filename says resume, metadata says source is github
        result = await classifier.classify(
            artifact_id=artifact_id,
            filename="my_resume.pdf",
            mime_type="application/pdf",
            file_size=1024,
            metadata={"source": "github"},
        )

        assert result.document_type == DocumentType.resume()
        assert result.confidence_level == ConfidenceLevel.HIGH
        assert result.provenance.evidence_location == "filename"

    async def test_rule_precedence_filename_overrides_mime(
        self, classifier: DeterministicDocumentClassifier
    ) -> None:
        """Verifies Filename rule (Priority 1) overrides MIME rule (Priority 3)."""
        artifact_id = uuid.uuid4()
        # Filename indicates certificate, mime indicates github json
        result = await classifier.classify(
            artifact_id=artifact_id,
            filename="degree_certificate.json",
            mime_type="application/vnd.github+json",
            file_size=2048,
        )

        assert result.document_type == DocumentType.certificate()
        assert result.confidence_level == ConfidenceLevel.HIGH
        assert result.provenance.evidence_location == "filename"

    async def test_filename_rules_all_document_types(
        self, classifier: DeterministicDocumentClassifier
    ) -> None:
        """Verifies all supported document types match via filename rules."""
        test_cases = [
            ("suyash_cv_2026.pdf", DocumentType.resume()),
            ("aws_certified_developer.pdf", DocumentType.certificate()),
            ("btech_marksheet_final.pdf", DocumentType.marksheet()),
            ("google_internship_offer_letter.pdf", DocumentType.internship_letter()),
            ("final_year_project_report.pdf", DocumentType.project_report()),
            ("my_design_portfolio.pdf", DocumentType.portfolio()),
            ("chronicle_ai_repo.zip", DocumentType.github_repository()),
        ]

        for filename, expected_type in test_cases:
            result = await classifier.classify(
                artifact_id=uuid.uuid4(),
                filename=filename,
                mime_type="application/pdf",
                file_size=5000,
            )
            assert result.document_type == expected_type
            assert result.confidence_level == ConfidenceLevel.HIGH
            assert result.classifier_version == DETERMINISTIC_CLASSIFIER_VERSION
            assert result.provenance.evidence_location == "filename"

    async def test_mime_rules_when_filename_generic(
        self, classifier: DeterministicDocumentClassifier
    ) -> None:
        """Verifies MIME rule (Priority 3) matches when filename is generic."""
        result = await classifier.classify(
            artifact_id=uuid.uuid4(),
            filename="data_export.json",
            mime_type="application/vnd.github+json",
            file_size=1200,
        )

        assert result.document_type == DocumentType.github_repository()
        assert result.confidence_level == ConfidenceLevel.MEDIUM
        assert result.provenance.evidence_location == "mime_type"

    async def test_metadata_rules_when_filename_and_mime_generic(
        self, classifier: DeterministicDocumentClassifier
    ) -> None:
        """Verifies Metadata rule (Priority 4) matches when filename and mime are generic."""
        result = await classifier.classify(
            artifact_id=uuid.uuid4(),
            filename="document.bin",
            mime_type="application/octet-stream",
            file_size=3000,
            metadata={"source": "github"},
        )

        assert result.document_type == DocumentType.github_repository()
        assert result.confidence_level == ConfidenceLevel.LOW
        assert result.provenance.evidence_location == "metadata"

    async def test_unknown_fallback(
        self, classifier: DeterministicDocumentClassifier
    ) -> None:
        """Verifies fallback to DocumentType.unknown() with LOW confidence when no rules match."""
        result = await classifier.classify(
            artifact_id=uuid.uuid4(),
            filename="random_unrecognized_file_123.xyz",
            mime_type="application/octet-stream",
            file_size=4096,
        )

        assert result.document_type == DocumentType.unknown()
        assert result.confidence_level == ConfidenceLevel.LOW
        assert result.provenance.evidence_location == "fallback"
        assert result.provenance.evidence_snippet == "No deterministic rules matched; falling back to Unknown"
