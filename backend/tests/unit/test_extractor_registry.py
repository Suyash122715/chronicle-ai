"""Unit tests for ExtractorRegistry, placeholder extractors, and dependency injection."""

import uuid
import pytest

from app.dependencies import get_extractor_registry
from app.domain.entities.artifact import Artifact
from app.domain.services.extractor_registry import ExtractorRegistry
from app.domain.value_objects.classification_result import ClassificationResult, ConfidenceLevel
from app.domain.value_objects.document_type import DocumentType, DocumentTypeEnum
from app.domain.value_objects.provenance import Provenance
from app.infrastructure.ai.certificate_extractor import CertificateExtractor
from app.infrastructure.ai.marksheet_extractor import MarksheetExtractor
from app.infrastructure.ai.resume_extractor import ResumeExtractor
from app.infrastructure.processing.placeholders import (
    BasePlaceholderExtractor,
    CertificateExtractor as PlaceholderCertificateExtractor,
    GitHubRepositoryExtractor,
    InternshipLetterExtractor,
    MarksheetExtractor as PlaceholderMarksheetExtractor,
    PortfolioExtractor,
    ProjectReportExtractor,
    ResumeExtractor as PlaceholderResumeExtractor,
    UnknownExtractor,
)


class TestExtractorRegistry:
    """Test suite for ExtractorRegistry resolution and registration logic."""

    def test_registration_and_lookup_all_types(self) -> None:
        """Verifies lookup resolves registered placeholder extractor classes for all document types."""
        registry = ExtractorRegistry()
        registry.register(DocumentType.resume(), ResumeExtractor)
        registry.register(DocumentType.certificate(), CertificateExtractor)
        registry.register(DocumentType.marksheet(), MarksheetExtractor)

        assert registry.get_extractor(DocumentType.resume()) == ResumeExtractor
        assert registry.get_extractor(DocumentType.certificate()) == CertificateExtractor
        assert registry.get_extractor(DocumentType.marksheet()) == MarksheetExtractor

    def test_resolve_fallback_to_default_extractor(self) -> None:
        """Verifies resolve() falls back to default_extractor when type is unregistered."""
        registry = ExtractorRegistry(default_extractor=UnknownExtractor)
        resolved = registry.resolve("UnregisteredType")
        assert resolved == UnknownExtractor

    def test_resolve_unregistered_raises_key_error_when_no_default(self) -> None:
        """Verifies resolve() raises KeyError if type is unregistered and no default is set."""
        registry = ExtractorRegistry()
        with pytest.raises(KeyError):
            registry.resolve("UnregisteredType")

    def test_has_extractor(self) -> None:
        """Verifies has_extractor returns True for registered types and False otherwise."""
        registry = ExtractorRegistry()
        registry.register(DocumentTypeEnum.RESUME, ResumeExtractor)
        registry.register(DocumentTypeEnum.CERTIFICATE, CertificateExtractor)
        registry.register(DocumentTypeEnum.MARKSHEET, MarksheetExtractor)

        assert registry.has_extractor(DocumentType.resume()) is True
        assert registry.has_extractor(DocumentType.certificate()) is True
        assert registry.has_extractor(DocumentType.marksheet()) is True
        assert registry.has_extractor(DocumentType.internship_letter()) is False

    @pytest.mark.asyncio
    async def test_placeholder_extractor_execution_returns_phase4_1_message(self) -> None:
        """Verifies placeholder extractors return placeholder message without performing extraction."""
        extractor = PlaceholderResumeExtractor()
        artifact_id = uuid.uuid4()
        artifact = Artifact(
            id=artifact_id,
            user_id=uuid.uuid4(),
            filename="resume.pdf",
            stored_filename="stored_resume.pdf",
            file_path="/storage/resume.pdf",
            file_size=1024,
            mime_type="application/pdf",
        )
        classification = ClassificationResult(
            document_type=DocumentType.resume(),
            confidence_level=ConfidenceLevel.HIGH,
            classifier_version="deterministic-1.0",
            classified_at=artifact.created_at,
            provenance=Provenance(artifact_id=artifact_id, confidence="HIGH"),
        )

        result = await extractor.extract(artifact, classification)
        assert result.llm_metadata["is_placeholder"] is True
        assert result.llm_metadata["message"] == "Not implemented in Phase 4.1"
        assert result.extractor_version == "ResumeExtractor"
        assert result.structured_data == {}

    def test_dependency_injection_provider(self) -> None:
        """Verifies FastAPI dependency injection provider returns pre-configured ExtractorRegistry."""
        registry = get_extractor_registry()
        assert isinstance(registry, ExtractorRegistry)
        assert registry.resolve(DocumentType.resume()) == ResumeExtractor
        assert registry.resolve(DocumentType.certificate()) == CertificateExtractor
        assert registry.resolve(DocumentType.marksheet()) == MarksheetExtractor
        assert registry.resolve(DocumentType.internship_letter()) == InternshipLetterExtractor
        assert registry.resolve(DocumentType.project_report()) == ProjectReportExtractor
        assert registry.resolve(DocumentType.portfolio()) == PortfolioExtractor
        assert registry.resolve(DocumentType.github_repository()) == GitHubRepositoryExtractor
        assert registry.resolve(DocumentType.unknown()) == UnknownExtractor
